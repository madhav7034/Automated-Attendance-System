import cv2
import numpy as np
import pickle
from datetime import datetime, date
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity

from models import db, Student, Attendance, FaceEmbedding

# =============================
# Initialize InsightFace
# =============================
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=0, det_size=(640, 640))

# =============================
# In-memory cache
# =============================
known_embeddings = []
known_students = []
marked_today = set()


# ======================================================
# ENROLLMENT
# ======================================================
def get_embedding(frame):
    faces = face_app.get(frame)
    if not faces:
        return None
    return faces[0].embedding.astype(np.float32)


# ======================================================
# LOAD KNOWN FACES (🔥 FIX HERE)
# ======================================================
def load_known_faces(course_id):
    global known_embeddings, known_students, marked_today

    known_embeddings = []
    known_students = []
    marked_today = set()

    students = Student.query.filter_by(course_id=course_id).all()

    for student in students:
        fe = FaceEmbedding.query.filter_by(student_id=student.id).first()
        if fe:
            # ✅ UNPICKLE + ENSURE FLOAT32
            emb = pickle.loads(fe.embedding)
            emb = np.asarray(emb, dtype=np.float32)

            known_embeddings.append(emb)
            known_students.append(student)

    print(f"[INFO] Loaded {len(known_students)} embeddings for course {course_id}")


# ======================================================
# ATTENDANCE
# ======================================================
def recognize_and_mark(frame, course_id):
    faces = face_app.get(frame)

    if not known_embeddings:
        return frame

    for face in faces:
        emb = face.embedding.reshape(1, -1).astype(np.float32)

        sims = cosine_similarity(emb, known_embeddings)[0]
        best_idx = int(np.argmax(sims))

        if sims[best_idx] > 0.5:
            student = known_students[best_idx]

            if student.id not in marked_today:
                exists = Attendance.query.filter_by(
                    student_id=student.id,
                    course_id=course_id,
                    date=date.today()
                ).first()

                if not exists:
                    attendance = Attendance(
                        student_id=student.id,
                        course_id=course_id,
                        date=date.today(),
                        time=datetime.now().time(),
                        status="Present"
                    )
                    db.session.add(attendance)
                    db.session.commit()

                marked_today.add(student.id)

            x1, y1, x2, y2 = map(int, face.bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(
                frame,
                f"{student.name} ✓",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

    return frame

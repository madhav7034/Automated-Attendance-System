from flask import Blueprint, render_template, request, redirect
from flask_login import login_required
import cv2
import pickle

from models import db, Student, Course, FaceEmbedding
from face_utils import get_embedding

# ❌ NO strict_slashes (older Flask compatibility)
enroll_bp = Blueprint("enroll", __name__)

CAMERA_INDEX = 0   # change to 1 if using external webcam


# ✅ support both /enroll and /enroll/
@enroll_bp.route("/enroll", methods=["GET", "POST"])
@enroll_bp.route("/enroll/", methods=["GET", "POST"])
@login_required
def enroll_student():
    courses = Course.query.all()

    if request.method == "POST":
        name = request.form.get("name")
        roll_no = request.form.get("roll_no")
        course_id = request.form.get("course_id")

        if not name or not roll_no or not course_id:
            return "Missing form data"

        course_id = int(course_id)

        cap = cv2.VideoCapture(CAMERA_INDEX)

        if not cap.isOpened():
            cap.release()
            return "Camera could not be opened"

        captured_frame = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.putText(
                frame,
                "Press Q to capture face",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow("Enroll Student", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                captured_frame = frame.copy()
                break

        cap.release()
        cv2.destroyAllWindows()

        if captured_frame is None:
            return "No frame captured"

        embedding = get_embedding(captured_frame)
        if embedding is None:
            return "No face detected. Try again."

        student = Student(
            name=name,
            roll_no=roll_no,
            course_id=course_id
        )

        db.session.add(student)
        db.session.commit()

        db.session.add(
            FaceEmbedding(
                student_id=student.id,
                embedding=pickle.dumps(embedding)
            )
        )
        db.session.commit()

        return redirect("/dashboard")

    return render_template("enroll.html", courses=courses)

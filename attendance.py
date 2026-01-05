from flask import Blueprint, render_template, request, redirect
from flask_login import login_required
import cv2

from models import Course
from face_utils import load_known_faces, recognize_and_mark

attendance_bp = Blueprint("attendance", __name__)

CAMERA_INDEX = 0   # change to 1 if needed


@attendance_bp.route("/take-attendance")
@login_required
def take_attendance():
    courses = Course.query.all()
    return render_template("take_attendance.html", courses=courses)


@attendance_bp.route("/start-attendance", methods=["POST"])
@login_required
def start_attendance():
    course_id = request.form.get("course_id")

    if not course_id or not course_id.isdigit():
        return redirect("/take-attendance")

    course_id = int(course_id)

    # Load known faces for selected course
    load_known_faces(course_id)

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        cap.release()
        return "Camera could not be opened"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = recognize_and_mark(frame, course_id)

        cv2.putText(
            frame,
            "Press Q to stop attendance",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        cv2.imshow("Live Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    return redirect("/dashboard")

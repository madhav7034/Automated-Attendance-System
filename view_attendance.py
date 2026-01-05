from datetime import date

from flask import Blueprint, render_template, request, Response
from flask_login import login_required

from models import Student, Course, Attendance

view_bp = Blueprint("view", __name__)

@view_bp.route("/view-attendance", methods=["GET"])
@login_required
def view_attendance():
    courses = Course.query.all()
    selected_course = request.args.get("course")
    selected_date = request.args.get("date", str(date.today()))

    records = []

    if selected_course:
        students = Student.query.filter_by(course_id=selected_course).all()

        for s in students:
            att = Attendance.query.filter_by(
                student_id=s.id,
                course_id=selected_course,
                date=selected_date
            ).first()

            records.append({
                "roll_no": s.roll_no,
                "name": s.name,
                "status": "Present" if att else "Absent",
                "time": att.time.strftime("%H:%M:%S") if att else "-"
            })

    return render_template(
        "view_attendance.html",
        courses=courses,
        records=records,
        selected_course=selected_course,
        selected_date=selected_date
    )


@view_bp.route("/download-attendance")
@login_required
def download_attendance():
    course_id = request.args.get("course")
    selected_date = request.args.get("date")

    course = Course.query.get(course_id)
    students = Student.query.filter_by(course_id=course_id).all()

    def generate():
        yield "Roll No,Name,Status,Time\n"
        for s in students:
            att = Attendance.query.filter_by(
                student_id=s.id,
                course_id=course_id,
                date=selected_date
            ).first()

            status = "Present" if att else "Absent"
            time = att.time.strftime("%H:%M:%S") if att else "-"
            yield f"{s.roll_no},{s.name},{status},{time}\n"

    filename = f"attendance_{course.name}_{selected_date}.csv"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

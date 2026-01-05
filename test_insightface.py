from insightface.app import FaceAnalysis

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0)   # 0 = GPU

print("InsightFace loaded successfully")

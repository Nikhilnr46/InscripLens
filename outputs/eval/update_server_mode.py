with open('api/server.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update run_analyse
t1 = """    if "multipart/form-data" in content_type:
        form = await request.form()
        if "use_demo" in form and str(form["use_demo"]).lower() in ("true", "1"):
            is_demo = True
        elif "file" in form:
            uploaded_file = form["file"]
            if hasattr(uploaded_file, "read"):
                raw = await uploaded_file.read()
                filename = "stone.png"
    else:
        query_demo = request.query_params.get("use_demo")
        if query_demo and query_demo.lower() in ("true", "1"):
            is_demo = True"""

r1 = """    mode = "standard"
    if "multipart/form-data" in content_type:
        form = await request.form()
        if "mode" in form:
            mode = str(form["mode"]).strip()
        if "use_demo" in form and str(form["use_demo"]).lower() in ("true", "1"):
            is_demo = True
        elif "file" in form:
            uploaded_file = form["file"]
            if hasattr(uploaded_file, "read"):
                raw = await uploaded_file.read()
                filename = "stone.png"
    else:
        query_demo = request.query_params.get("use_demo")
        if query_demo and query_demo.lower() in ("true", "1"):
            is_demo = True
        query_mode = request.query_params.get("mode")
        if query_mode:
            mode = query_mode.strip()

    mode = "high_accuracy" if mode.lower() in ("high_accuracy", "high-accuracy", "highaccuracy") else "standard\""""

assert t1 in c, "t1 not found in api/server.py"
c = c.replace(t1, r1)

t2 = """    # Call existing analyse function
    try:
        record = analyse(raw, filename, DATA_DIR)
    except Exception:
        raise HTTPException(status_code=500, detail="Enhancement analysis could not be completed.")

    # Compute candidate boxes from generated mask
    mask_path = Path(record["mask_path"])
    with Image.open(mask_path) as mask:
        boxes = candidates(mask)
        analysis_width, analysis_height = mask.size

    # Clean display name: never expose file names
    display_name = "Nagavara demonstration stone" if is_demo else "Uploaded photograph"
    run_id = record["id"]

    return {
        "id": run_id,
        "display_name": display_name,
        "is_demo": is_demo,
        "sha256": record["sha256"],
        "image_url": f"/app_data/{run_id}/input.png",
        "mask_url": f"/app_data/{run_id}/mask.png",
        "width": analysis_width,
        "height": analysis_height,
        "boxes": boxes,
        "candidate_count": len(boxes),
        "created": record["created"]
    }"""

r2 = """    # Call existing analyse function with optional mode
    try:
        record = analyse(raw, filename, DATA_DIR, mode=mode)
    except Exception:
        raise HTTPException(status_code=500, detail="Enhancement analysis could not be completed.")

    # Compute candidate boxes from generated mask
    mask_path = Path(record["mask_path"])
    with Image.open(mask_path) as mask:
        boxes = candidates(mask)
        analysis_width, analysis_height = mask.size

    # Clean display name: never expose file names
    display_name = "Nagavara demonstration stone" if is_demo else "Uploaded photograph"
    run_id = record["id"]
    effective_mode = record.get("mode", mode)
    mode_label = record.get("mode_label", "High accuracy" if effective_mode == "high_accuracy" else "Standard")

    payload = {
        "id": run_id,
        "display_name": display_name,
        "is_demo": is_demo,
        "sha256": record["sha256"],
        "image_url": f"/app_data/{run_id}/input.png",
        "mask_url": f"/app_data/{run_id}/mask.png",
        "width": analysis_width,
        "height": analysis_height,
        "boxes": boxes,
        "candidate_count": len(boxes),
        "created": record["created"],
        "mode": effective_mode,
        "mode_label": mode_label
    }
    if record.get("fallback_note"):
        payload["fallback_note"] = record["fallback_note"]

    return payload"""

assert t2 in c, "t2 not found in api/server.py"
c = c.replace(t2, r2)

# 2. Update get_analysis_history
t3 = """@app.get("/api/history")
def get_analysis_history():
    \"\"\"Retrieve local analysis run history stripped of absolute paths and internal filenames.\"\"\"
    try:
        raw_history = history(DATA_DIR)
        sanitized = []
        for r in raw_history:
            fname = (r.get("filename") or "").lower()
            if "hs027" in fname or "demo" in fname:
                display_name = "Nagavara demonstration stone"
            else:
                display_name = "Uploaded photograph"

            sanitized.append({
                "id": r["id"],
                "created": r["created"],
                "display_name": display_name,
                "image_url": f"/app_data/{r['id']}/input.png",
                "mask_url": f"/app_data/{r['id']}/mask.png",
                "sha256": r.get("sha256", "")
            })
        return sanitized
    except Exception:
        raise HTTPException(status_code=500, detail="Analysis history could not be retrieved.")"""

r3 = """@app.get("/api/history")
def get_analysis_history():
    \"\"\"Retrieve local analysis run history stripped of absolute paths and internal filenames.\"\"\"
    try:
        raw_history = history(DATA_DIR)
        sanitized = []
        for r in raw_history:
            fname = (r.get("filename") or "").lower()
            if "hs027" in fname or "demo" in fname:
                display_name = "Nagavara demonstration stone"
            else:
                display_name = "Uploaded photograph"

            details = {}
            if r.get("details"):
                try:
                    details = json.loads(r["details"])
                except Exception:
                    pass
            mode = details.get("mode", "standard")
            mode_label = details.get("mode_label", "High accuracy" if mode == "high_accuracy" else "Standard")

            item = {
                "id": r["id"],
                "created": r["created"],
                "display_name": display_name,
                "image_url": f"/app_data/{r['id']}/input.png",
                "mask_url": f"/app_data/{r['id']}/mask.png",
                "sha256": r.get("sha256", ""),
                "mode": mode,
                "mode_label": mode_label
            }
            if details.get("fallback_note"):
                item["fallback_note"] = details["fallback_note"]
            sanitized.append(item)
        return sanitized
    except Exception:
        raise HTTPException(status_code=500, detail="Analysis history could not be retrieved.")

@app.get("/api/export/{run_id}")
def get_run_export(run_id: str):
    \"\"\"Export analysis metadata and character reviews without internal file paths.\"\"\"
    try:
        data = review_export(run_id, DATA_DIR)
        if "analysis" in data:
            a = data["analysis"]
            fname = (a.get("filename") or "").lower()
            a["filename"] = "Nagavara demonstration stone" if ("hs027" in fname or "demo" in fname) else "Uploaded photograph"
            a["image_url"] = f"/app_data/{run_id}/input.png"
            a["mask_url"] = f"/app_data/{run_id}/mask.png"
            a.pop("image_path", None)
            a.pop("mask_path", None)
            details = a.get("details", {})
            if isinstance(details, dict):
                details["mode"] = details.get("mode", "standard")
                details["mode_label"] = details.get("mode_label", "High accuracy" if details["mode"] == "high_accuracy" else "Standard")
        return data
    except ValueError:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    except Exception:
        raise HTTPException(status_code=500, detail="Review export could not be generated.")"""

assert t3 in c, "t3 not found in api/server.py"
c = c.replace(t3, r3)

with open('api/server.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Successfully updated api/server.py with mode handling and export')


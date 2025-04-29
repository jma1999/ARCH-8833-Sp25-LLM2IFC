def extract_code_block(full_text):
    """
    Return only the lines between the first pair of triple backticks (```).
    If no triple backticks found, we fallback to returning the entire string.
    """
    lines = full_text.splitlines()
    code_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            code_lines.append(line)

    if code_lines:
        return "\n".join(code_lines)
    else:
        return full_text


def parse_obj_text(obj_str):
    vertices = []
    faces = []

    for line in obj_str.splitlines():
        line = line.strip()

        if line.startswith("v "):
            parts = line.split()
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            vertices.append((x, y, z))

        elif line.startswith("f "):
            parts = line.split()
            idxs = [int(i) for i in parts[1:]]
            faces.append(idxs)

    return vertices, faces


def main():
    # 1) Read the entire text from file with messy llm output
    with open("obj_mess.txt", "r", encoding="utf-8") as f:
        file_content = f.read()

    # 2) Extract the lines between triple backticks
    obj_text = extract_code_block(file_content)

    # Debug: See what was extracted
    print("=== Code Block Extracted ===\n", obj_text, "\n=== END ===")

    # 3) Parse the extracted text
    vertices, faces = parse_obj_text(obj_text)
    print(f"Parsed {len(vertices)} vertices, {len(faces)} faces")

    # 4) Write them to a new file
    with open("parsed_mesh.txt", "w", encoding="utf-8") as out_f:
        out_f.write("=== Parsed Mesh Data ===\n\n")

        out_f.write("Vertices:\n")
        for (x, y, z) in vertices:
            out_f.write(f"{x} {y} {z}\n")

        out_f.write("\nFaces:\n")
        for face_indices in faces:
            out_f.write(" ".join(str(i) for i in face_indices) + "\n")

    print("Done. Check parsed_mesh.txt for results.")


if __name__ == "__main__":
    main()

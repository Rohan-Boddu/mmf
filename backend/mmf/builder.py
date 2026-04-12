import zipfile
import os

def build_mmf(source_folder, output_folder, output_name="assistant.mmf"):
    """
    Builds a .mmf file from source_folder into output_folder.
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_path = os.path.join(output_folder, output_name)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                full_path = os.path.join(root, file)

                # Keep relative structure clean
                arcname = os.path.relpath(full_path, source_folder)

                zipf.write(full_path, arcname)

    print(f"[MMF BUILDER] Built: {output_path}")

if __name__ == "__main__":
    # Define where the folder is and where the file should go
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_dir = os.path.join(base_dir, "assistant.mmf")
    output_name = "assistant_export.mmf"
    
    # Run the function!
    build_mmf(source_folder=source_dir, output_folder=base_dir, output_name=output_name)
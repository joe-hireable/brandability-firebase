import { useState } from "react";
import { Upload } from "lucide-react";
import { ref, uploadBytes } from "firebase/storage";

import { Button } from "./ui/button";
import { storage } from "../firebase";

export function FileUpload() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!files) return;

    setUploading(true);
    setMessage("Uploading...");

    try {
      for (const file of Array.from(files)) {
        const storageRef = ref(storage, `uploads/${file.name}`);
        await uploadBytes(storageRef, file);
      }
      setMessage("Files uploaded successfully!");
      setFiles(null);
    } catch (error) {
      console.error("Error uploading files:", error);
      setMessage("Error uploading files.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg">
      <input
        type="file"
        multiple
        onChange={handleFileChange}
        className="hidden"
        id="file-upload"
      />
      <label
        htmlFor="file-upload"
        className="flex flex-col items-center justify-center w-full h-full cursor-pointer"
      >
        <Upload className="w-12 h-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          Drag & drop files here, or click to select files
        </p>
      </label>
      {files && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold">Selected Files:</h3>
          <ul className="mt-2 list-disc list-inside">
            {Array.from(files).map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}
      <Button onClick={handleUpload} disabled={!files || uploading} className="mt-4">
        {uploading ? "Uploading..." : "Upload"}
      </Button>
      {message && <p className="mt-4 text-sm">{message}</p>}
    </div>
  );
}
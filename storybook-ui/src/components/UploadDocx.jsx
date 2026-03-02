// import { useState } from "react";
// import { uploadDocx } from "../api/backend";
// import "../styles/global.css";
// export default function UploadDocx({ onSuccess }) {
//   const [file, setFile] = useState(null);
//   const [loading, setLoading] = useState(false);

//   const handleUpload = async () => {
//     if (!file) return alert("Please select a DOCX file");

//     setLoading(true);
//     try {
//       const res = await uploadDocx(file);
//       onSuccess(res.data);
//       console.log("Upload response:", res);
//     } catch (err) {
//       alert("Upload failed");
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="card upload-card">
//   <h2>Upload Storybook</h2>
//   <p className="muted">
//     Upload a DOCX file to generate scenes and illustrations.
//   </p>

//   <input
//     type="file"
//     accept=".docx"
//     onChange={(e) => setFile(e.target.files[0])}
//   />
//   {/* <select onChange={(e) => setSelectedDoc(e.target.value)}>
//   <option value="">Select document</option>
//   <option value="storybook_1.docx">Storybook 1</option>
//   <option value="storybook_2.docx">Storybook 2</option>
// </select> */}


//   <button className="primary" onClick={handleUpload} disabled={loading}>
//     {loading ? "Processing…" : "Upload & Analyze"}
//   </button>
// </div>

//   );
// }


import { useState } from "react";
import { uploadDocx } from "../api/backend";
import "../styles/global.css";

export default function UploadDocx({ onSuccess }) {
  const [uploadType, setUploadType] = useState(""); // predefined | custom
  const [selectedDoc, setSelectedDoc] = useState("");
  const [customFile, setCustomFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    try {
      let fileToUpload = null;

      if (uploadType === "predefined") {
        if (!selectedDoc) {
          alert("Please select a predefined document");
          return;
        }

        // fetch predefined doc
        const response = await fetch(`/docs/${selectedDoc}`);
        const blob = await response.blob();

        fileToUpload = new File([blob], selectedDoc, {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        });
      }

      if (uploadType === "custom") {
        if (!customFile) {
          alert("Please upload a DOCX file");
          return;
        }
        fileToUpload = customFile;
      }

      if (!fileToUpload) {
        alert("Please select an upload option");
        return;
      }

      setLoading(true);
      const res = await uploadDocx(fileToUpload);
      onSuccess(res.data);
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card upload-card">
      <h2>Upload Storybook</h2>
      <p className="muted">
        Choose a predefined storybook or upload your own DOCX file.
      </p>

      {/* 🔘 Predefined Option */}
      <label>
        <input
          type="radio"
          name="uploadType"
          value="predefined"
          checked={uploadType === "predefined"}
          onChange={() => setUploadType("predefined")}
        />
        Use predefined storybook
      </label>

      {uploadType === "predefined" && (
        <div className="radio-group">
          <label>
            <input
              type="radio"
              name="storybook"
              value="Bailey and Beau's Imaginative Science Extravaganza-FInal (1).docx"
              checked={
                selectedDoc ===
                "Bailey and Beau's Imaginative Science Extravaganza-FInal (1).docx"
              }
              onChange={(e) => setSelectedDoc(e.target.value)}
            />
            Bailey and Beau's Imaginative Science Extravaganza
          </label>
          <br />
          <label>
            <input
              type="radio"
              name="storybook"
              value="Title_Bailey and Beaus Epic Explorations Partners in Discovery.docx"
              checked={
                selectedDoc ===
                "Title_Bailey and Beaus Epic Explorations Partners in Discovery.docx"
              }
              onChange={(e) => setSelectedDoc(e.target.value)}
            />
            Bailey and Beaus Epic Explorations
          </label>
        </div>
      )}

      <br />

      {/* 🔘 Custom Upload Option */}
      <label>
        <input
          type="radio"
          name="uploadType"
          value="custom"
          checked={uploadType === "custom"}
          onChange={() => setUploadType("custom")}
        />
        Upload your own document
      </label>

      {uploadType === "custom" && (
        <input
          type="file"
          accept=".docx"
          onChange={(e) => setCustomFile(e.target.files[0])}
        />
      )}

      <br />

      <button className="primary" onClick={handleUpload} disabled={loading}>
        {loading ? "Processing…" : "Upload & Analyze"}
      </button>
    </div>
  );
}

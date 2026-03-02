import { useState } from "react";
import { updateScenesJson } from "../api/backend";
import "../styles/BookSummary.css";

export default function BookSummary({ data }) {
  const [isEditing, setIsEditing] = useState(false);
  const [jsonText, setJsonText] = useState(
    JSON.stringify(data, null, 2)
  );
  const [saving, setSaving] = useState(false);

  if (!data) return null;

  const handleSave = async () => {
  try {
    setSaving(true);

    const parsed = JSON.parse(jsonText);

      // Handle possible schema change: "page" -> "pages"
    if (parsed.page && !parsed.pages) {
      parsed.pages = parsed.page;
      delete parsed.page;
    }

    await updateScenesJson(data.book_file_id, parsed);

    alert("scenes.json updated successfully");
    setIsEditing(false);
  } catch (err) {
    alert("Invalid JSON or save failed");
    console.error(err);
  } finally {
    setSaving(false);
  }
};


  const handleDownload = () => {
    const blob = new Blob([jsonText], {
      type: "application/json"
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "scenes.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card">

      {/* Header */}
      <div className="book-header-wrapper">
        <div className="book-header">
          <h3 className="book-title">{data.book_title}</h3>
          <div className="book-meta">
            <span>Total Pages: {data.pages_count}</span>
            <span>•</span>
            <span>Book ID: {data.book_file_id}</span>
          </div>
        </div>
      </div>

      {/* JSON Viewer */}
      <div className="scene-json-wrapper">
        <div className="scene-json-container">

          <div className="scene-json-header">
            <span>Scene Configuration (scenes.json)</span>

            <div className="actions">
              {!isEditing && (
                <button onClick={() => setIsEditing(true)}>
                  Edit
                </button>
              )}

              {isEditing && (
                <button
                  className="primary"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "Saving..." : "Save"}
                </button>
              )}

              <button onClick={handleDownload}>
                Download
              </button>
            </div>
          </div>

          {/* JSON Box */}
          {isEditing ? (
            <textarea
              className="scene-json-editor"
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
            />
          ) : (
            <pre className="scene-json-box">
              {jsonText}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

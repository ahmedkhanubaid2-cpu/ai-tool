import { useState, useEffect } from "react";
import { getBookStatus, generatePageScene, updateScenesJson, getSystemUsage } from "../api/backend";
import "../styles/BookSummary.css";

export default function BookSummary({ data }) {
  const [bookId, setBookId] = useState(data.book_id);
  const [extractedPages, setExtractedPages] = useState(data.extracted_pages || []);
  const [generatedScenes, setGeneratedScenes] = useState([]);
  const [loadingPages, setLoadingPages] = useState({}); // { pageNumber: boolean }
  const [isEditingJson, setIsEditingJson] = useState(false);
  const [jsonText, setJsonText] = useState("");
  const [usage, setUsage] = useState({ llm_requests: 0, image_requests: 0 });

  // Initial load of book status
  useEffect(() => {
    if (bookId) {
      console.log(`[BookSummary] Initializing for bookId: ${bookId}`);
      refreshStatus();
      updateUsage();
    }
  }, [bookId]);

  const updateUsage = async () => {
    try {
      const res = await getSystemUsage();
      setUsage(res.data);
    } catch (err) {
      console.error("[BookSummary] Failed to fetch usage stats", err);
    }
  };

  const refreshStatus = async () => {
    try {
      console.log(`[BookSummary] Refreshing status for ${bookId}...`);
      const res = await getBookStatus(bookId);
      setExtractedPages(res.data.extracted_pages);
      setGeneratedScenes(res.data.generated_scenes);
      setJsonText(JSON.stringify({
        book_title: res.data.book_title,
        pages: res.data.generated_scenes
      }, null, 2));
      console.log(`[BookSummary] Status refreshed. Pages: ${res.data.extracted_pages.length}, Scenes: ${res.data.generated_scenes.length}`);
    } catch (err) {
      console.error("[BookSummary] Failed to fetch book status", err);
    }
  };

  const handleGeneratePage = async (pageNumber) => {
    console.log(`[BookSummary] Triggering generation for page ${pageNumber}`);
    setLoadingPages(prev => ({ ...prev, [pageNumber]: true }));
    try {
      await generatePageScene(bookId, pageNumber);
      console.log(`[BookSummary] Generation success for page ${pageNumber}`);
      await refreshStatus();
      updateUsage();
    } catch (err) {
      console.error(`[BookSummary] Generation failed for page ${pageNumber}:`, err);
      alert(`Failed to generate page ${pageNumber}. Check console for details.`);
    } finally {
      setLoadingPages(prev => ({ ...prev, [pageNumber]: false }));
    }
  };

  const handleGenerateAll = async () => {
    for (const page of extractedPages) {
      // Simple sequential loop for demo purposes
      await handleGeneratePage(page.page_number);
    }
  };

  const handleSaveJson = async () => {
    try {
      const parsed = JSON.parse(jsonText);
      await updateScenesJson(bookId, parsed);
      alert("scenes.json updated");
      setIsEditingJson(false);
      refreshStatus();
    } catch (err) {
      alert("Invalid JSON");
    }
  };

  if (!bookId) return null;

  return (
    <div className="book-summary-container">
      {/* Header */}
      <div className="book-header-wrapper">
        <div className="book-header">
          <h3 className="book-title">{data.book_title}</h3>
          <div className="book-meta">
            <span>Total Pages: {extractedPages.length}</span>
            <span>•</span>
            <span>Book ID: {bookId}</span>
          </div>
          <div className="api-credits-badge">
            <span title="Total LLM requests made this session">📝 LLM Requests: <strong>{usage.llm_requests}</strong></span>
            <span title="Total Image requests made this session">🖼️ Image Requests: <strong>{usage.image_requests}</strong></span>
          </div>
          <button
            className="primary"
            style={{ marginTop: '15px' }}
            onClick={handleGenerateAll}
            disabled={Object.values(loadingPages).some(v => v)}
          >
            Generate All Scenes
          </button>
        </div>
      </div>

      {/* Page List - Milestone 1 Refactor */}
      <div className="page-list">
        {extractedPages.map((page) => {
          const scene = generatedScenes.find(s => s.page_number === page.page_number);
          const isLoading = loadingPages[page.page_number];

          return (
            <div key={page.page_number} className="page-card">
              <div className="page-card-header">
                <h4>Page {page.page_number}</h4>
                {scene ? (
                  <span className="generated-badge">Scene Generated</span>
                ) : (
                  <span className="pending-badge">Pending Generation</span>
                )}
              </div>

              <div className="page-card-content">
                <div className="raw-text-section">
                  <h5>Document Text</h5>
                  <div className="raw-text">{page.page_text}</div>
                </div>

                {scene && (
                  <div className="scene-details">
                    <div className="scene-field">
                      <label>Setting</label>
                      <p>{scene.setting} - {scene.time_of_day}</p>
                    </div>
                    <div className="scene-field">
                      <label>Mood</label>
                      <p>{scene.mood}</p>
                    </div>
                    <div className="scene-field">
                      <label>Composition Notes</label>
                      <p>{scene.composition_notes}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="regenerate-actions">
                {isLoading ? (
                  <div className="loading-inline">
                    <div className="spinner-small"></div>
                    <span>{scene ? "Regenerating..." : "Generating..."}</span>
                  </div>
                ) : (
                  <button
                    className={scene ? "secondary" : "primary"}
                    onClick={() => handleGeneratePage(page.page_number)}
                  >
                    {scene ? "✨ Regenerate Scene" : "🚀 Generate Scene"}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Advanced JSON Mode */}
      <div className="scene-json-wrapper">
        <div className="scene-json-container">
          <div className="scene-json-header">
            <span>Advanced: scenes.json</span>
            <div className="actions">
              <button onClick={() => setIsEditingJson(!isEditingJson)}>
                {isEditingJson ? "Cancel" : "Edit JSON"}
              </button>
              {isEditingJson && (
                <button className="primary" onClick={handleSaveJson}>Save</button>
              )}
            </div>
          </div>
          {isEditingJson ? (
            <textarea
              className="scene-json-editor"
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
            />
          ) : (
            <pre className="scene-json-box">{jsonText}</pre>
          )}
        </div>
      </div>
    </div>
  );
}

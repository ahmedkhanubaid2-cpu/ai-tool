import { useState, useEffect, useRef } from "react";
import { generateImages, getImageGenerationStatus, API_BASE } from "../api/backend";
import "../styles/ImageGeneration.css";

export default function ImageGeneration({ bookId }) {
  const [loading, setLoading] = useState(false);
  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Real-time progress state
  const [progress, setProgress] = useState(0);
  const [counts, setCounts] = useState({ generated: 0, total: 0 });
  const pollInterval = useRef(null);

  useEffect(() => {
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, []);

  const startPolling = () => {
    if (pollInterval.current) clearInterval(pollInterval.current);

    pollInterval.current = setInterval(async () => {
      try {
        const res = await getImageGenerationStatus(bookId);
        const { generated_count, total_pages, generated_pages, images_folder } = res.data;

        setCounts({ generated: generated_count, total: total_pages });

        if (total_pages > 0) {
          setProgress(Math.round((generated_count / total_pages) * 100));
        }

        const API_HOST = API_BASE;
        const baseUrl = `${API_HOST}/media/` + images_folder.replace(/^data[\\/]/, "").replaceAll("\\", "/");

        if (generated_pages && generated_pages.length > 0) {
          const imageUrls = generated_pages.map(page => ({
            page: page,
            url: `${baseUrl}/page_${String(page).padStart(3, "0")}.png`
          }));

          setImages(imageUrls);
        }

        // Stop polling if completely done
        if (generated_count >= total_pages && total_pages > 0) {
          clearInterval(pollInterval.current);
          setLoading(false);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 2000);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setImages([]);
    setCurrentIndex(0);
    setProgress(0);
    setCounts({ generated: 0, total: 0 });

    try {
      await generateImages(bookId);
      startPolling();
    } catch (err) {
      console.error(err);
      alert("Image generation failed to start.");
      setLoading(false);
    }
  };

  const nextImage = () => {
    if (currentIndex < images.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const prevImage = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const downloadImage = async (img) => {
    const response = await fetch(img.url);
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = `page_${String(img.page).padStart(3, "0")}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  };

  const downloadAllImages = async () => {
    for (const img of images) {
      try {
        await downloadImage(img);
        await new Promise((res) => setTimeout(res, 300));
      } catch (err) {
        console.error("Failed to download:", img.url, err);
      }
    }
  };

  return (
    <div className="image-viewer-container">
      <button className="primary" onClick={handleGenerate} disabled={loading}>
        {loading ? "Generating Illustrations..." : "Generate Illustrations"}
      </button>

      {/* Progress Bar & Real-time Counts */}
      {loading && (
        <div className="progress-container" style={{ marginTop: '20px', maxWidth: '600px', margin: '20px auto 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
            <span>Generating progress...</span>
            <span>{counts.generated} / {counts.total} images</span>
          </div>
          <div style={{ width: '100%', backgroundColor: '#e5e7eb', borderRadius: '8px', overflow: 'hidden', height: '12px' }}>
            <div style={{
              height: '100%',
              backgroundColor: '#4f46e5',
              width: `${progress}%`,
              transition: 'width 0.4s ease'
            }}></div>
          </div>
        </div>
      )}

      {/* Image Viewer */}
      {images.length > 0 && (
        <div className="viewer" style={{ opacity: loading ? 0.7 : 1 }}>
          <button
            className="nav-button"
            onClick={prevImage}
            disabled={currentIndex === 0}
          >
            ‹
          </button>

          <div className="image-wrapper">
            <button
              className="download-single"
              onClick={() => downloadImage(images[currentIndex])}
              title="Download image"
            >
              ⬇
            </button>

            <img
              src={images[currentIndex]?.url}
              alt={`Page ${images[currentIndex]?.page}`}
            />

            <div className="page-indicator">
              Page {images[currentIndex]?.page} of {images[images.length - 1]?.page || images.length}
            </div>
          </div>

          <button
            className="nav-button"
            onClick={nextImage}
            disabled={currentIndex >= images.length - 1}
          >
            ›
          </button>
        </div>
      )}

      {images.length > 0 && !loading && (
        <div className="download-all-wrapper">
          <button className="primary outline" onClick={downloadAllImages}>
            Download All Images
          </button>
        </div>
      )}

    </div>
  );
}

import { useState } from "react";
import { generateImages } from "../api/backend";
import "../styles/ImageGeneration.css";
import {API_BASE} from "../api/backend";
export default function ImageGeneration({ bookId }) {
  const [loading, setLoading] = useState(false);
  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleGenerate = async () => {
    setLoading(true);
    setImages([]);
    setCurrentIndex(0);

    try {
      const response = await generateImages(bookId);

      const API_HOST = API_BASE;
      const { images_folder, generated_count } = response.data;

      const baseUrl =
        `${API_HOST}/media/` +
        images_folder
          .replace(/^data[\\/]/, "")
          .replaceAll("\\", "/");

      const imageUrls = Array.from({ length: generated_count }, (_, i) => ({
        page: i + 1,
        url: `${baseUrl}/page_${String(i + 1).padStart(3, "0")}.png`,
      }));

      setImages(imageUrls);
    } catch (err) {
      console.error(err);
      alert("Image generation failed. Please try again.");
    } finally {
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
      await new Promise((res) => setTimeout(res, 300)); // browser-safe delay
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

      {/* Loader Overlay */}
      {loading && (
        <div className="loader-overlay">
          <div className="spinner"></div>
          <p>Generating illustrations. Please wait…</p>
        </div>
      )}

      {/* Image Viewer */}
      {images.length > 0 && !loading && (
        <div className="viewer">
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
              src={images[currentIndex].url}
              alt={`Page ${images[currentIndex].page}`}
            />

            <div className="page-indicator">
              Page {images[currentIndex].page} of {images.length}
            </div>
          </div>

          <button
            className="nav-button"
            onClick={nextImage}
            disabled={currentIndex === images.length - 1}
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

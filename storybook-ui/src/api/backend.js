import axios from "axios";

export const API_BASE = "http://76.13.108.33:8001";
//const API_BASE = "http://127.0.0.1:8001";

/**
 * Upload predefined DOCX file
 */
export const uploadDocx = (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return axios.post(`${API_BASE}/v1/upload-docx`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

/**
 * Start Gemini image generation (returns only when ALL images are done)
 */
export const generateImages = (bookId) => {
  return axios.post(
    `${API_BASE}/v1/books/${bookId}/generate-images-gemini`
  );
};

/*  Update scenes.json */
export const updateScenesJson = (bookId, payload) => {
  return axios.post(
    `${API_BASE}/v1/books/${bookId}/scenes`,
    payload,
    { headers: { "Content-Type": "application/json" } }
  );
};

/**
 * Poll image generation progress (for progress bar)
 * Backend must return: total_images, completed_images
 */
// export const getImageGenerationStatus = (bookId) => {
//   return axios.get(
//     `${API_BASE}/v1/books/${bookId}/images/status`
//   );
// };

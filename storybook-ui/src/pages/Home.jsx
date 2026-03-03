import { useState } from "react";
import UploadDocx from "../components/UploadDocx";
import BookSummary from "../components/BookSummary";
import ImageGeneration from "../components/ImageGeneration";

import "../styles/global.css";

export default function Home() {
  const [book, setBook] = useState(null);
  const [status, setStatus] = useState("upload");

  const resetFlow = () => {
    setBook(null);
    setStatus("upload");
  };

  return (
    <div className="container">

      {status !== "upload" && (
        <div style={{ textAlign: "right", marginBottom: "12px" }}>
          <button className="secondary" onClick={resetFlow}>
            Choose a Different Document
          </button>
        </div>
      )}

      {status === "upload" && (
        <UploadDocx
          onSuccess={(b) => {
            setBook(b);
            setStatus("summary");
          }}
        />
      )}

      {status === "summary" && (
        <>
          <BookSummary data={book} />
          <ImageGeneration
            bookId={book.book_id}
            onStart={() => setStatus("generating")}
          />
        </>
      )}


    </div>
  );
}


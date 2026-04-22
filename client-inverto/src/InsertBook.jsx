import { useState, useRef } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "";

function InputField({ label, type = "text", value, onChange, placeholder, required = false, name }) {
  return (
    <div className="form-field">
      <label>{label} {required && <span className="required">*</span>}</label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className="form-input"
      />
    </div>
  );
}

function TextAreaField({ label, value, onChange, placeholder, required = false }) {
  return (
    <div className="form-field">
      <label>{label} {required && <span className="required">*</span>}</label>
      <textarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className="form-textarea"
        rows="4"
      />
    </div>
  );
}

function TagsField({ label, value, onChange, placeholder, required = false }) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const newTag = e.target.value.trim();
      if (newTag) {
        const tags = value ? [...value, newTag] : [newTag];
        onChange(tags);
        e.target.value = "";
      }
    }
  };

  const removeTag = (index) => {
    onChange(value.filter((_, i) => i !== index));
  };

  return (
    <div className="form-field">
      <label>{label} {required && <span className="required">*</span>}</label>
      <div className="tags-input-container">
        <input
          type="text"
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="form-input tags-input"
        />
        <div className="tags-list">
          {value && value.length > 0 && value.map((tag, idx) => (
            <span key={idx} className="tag-chip">
              {tag}
              <button
                type="button"
                className="tag-remove"
                onClick={() => removeTag(idx)}
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function InsertBook() {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    publisher: "",
    publication_year: new Date().getFullYear(),
    edition: 1,
    language: "English",
    isbn: "",
    pages: 0,
    book_authors: [],
    book_tags: [],
    book_categories: []
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const formRef = useRef(null);

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === "number" ? parseInt(value) : value
    }));
  };

  const handleTagsChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const response = await axios.post(`${API_BASE}/api/book/create`, formData);
      setIsError(false);
      setMessage("✓ Book added successfully! Book ID: " + response.data.id);

      setTimeout(() => {
        setFormData({
          title: "",
          description: "",
          publisher: "",
          publication_year: new Date().getFullYear(),
          edition: 1,
          language: "English",
          isbn: "",
          pages: 0,
          book_authors: [],
          book_tags: [],
          book_categories: []
        });
        setMessage("");
      }, 2000);
    } catch (err) {
      setIsError(true);
      setMessage("✗ Error adding book: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="insert-container">
      <div className="insert-header">
        <div className="insert-eyebrow">Add New Book</div>
        <h1 className="insert-title">Insert Book Details</h1>
        <p className="insert-subtitle">
          Fill in the book information to add it to the library database
        </p>
      </div>

      <div className="form-wrapper">
        <form onSubmit={handleSubmit} ref={formRef} className="insert-form">

          {/* Basic Info */}
          <div className="form-section">
            <h2 className="section-title">📚 Basic Information</h2>
            <div className="form-grid form-grid-2">
              <InputField
                label="Title"
                value={formData.title}
                onChange={handleInputChange}
                name="title"
                placeholder="Enter book title"
                required
              />
              <InputField
                label="Publisher"
                value={formData.publisher}
                onChange={handleInputChange}
                name="publisher"
                placeholder="Enter publisher name"
                required
              />
            </div>

            <TextAreaField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Enter book description"
              required
            />
          </div>

          {/* Publication Details */}
          <div className="form-section">
            <h2 className="section-title">📅 Publication Details</h2>

            <div className="form-grid form-grid-3">
              <InputField
                label="Publication Year"
                type="number"
                value={formData.publication_year}
                onChange={handleInputChange}
                name="publication_year"
                required
              />
              <InputField
                label="Edition"
                type="number"
                value={formData.edition}
                onChange={handleInputChange}
                name="edition"
                required
              />
              <InputField
                label="Language"
                value={formData.language}
                onChange={handleInputChange}
                name="language"
                required
              />
            </div>

            {/* NEW FIELDS */}
            <div className="form-grid form-grid-2">
              <InputField
                label="ISBN"
                value={formData.isbn}
                onChange={handleInputChange}
                name="isbn"
                placeholder="Enter ISBN"
                required
              />
              <InputField
                label="Pages"
                type="number"
                value={formData.pages}
                onChange={handleInputChange}
                name="pages"
                placeholder="Enter number of pages"
                required
              />
            </div>
          </div>

          {/* Metadata */}
          <div className="form-section">
            <h2 className="section-title">🏷️ Metadata</h2>

            <div className="form-grid form-grid-2">
              <TagsField
                label="Authors"
                value={formData.book_authors}
                onChange={(value) => handleTagsChange("book_authors", value)}
                placeholder="Type author and press Enter"
                required
              />
              <TagsField
                label="Categories"
                value={formData.book_categories}
                onChange={(value) => handleTagsChange("book_categories", value)}
                placeholder="Type category and press Enter"
              />
            </div>

            <TagsField
              label="Tags"
              value={formData.book_tags}
              onChange={(value) => handleTagsChange("book_tags", value)}
              placeholder="Type tag and press Enter"
            />
          </div>

          {/* Message */}
          {message && (
            <div className={`message-box ${isError ? "message-error" : "message-success"}`}>
              {message}
            </div>
          )}

          {/* Actions */}
          <div className="form-actions">
            <button type="submit" disabled={loading} className="btn-submit">
              {loading ? "Adding Book..." : "Add Book"}
            </button>

            <button
              type="reset"
              className="btn-reset"
              onClick={() =>
                setFormData({
                  title: "",
                  description: "",
                  publisher: "",
                  publication_year: new Date().getFullYear(),
                  edition: 1,
                  language: "English",
                  isbn: "",
                  pages: 0,
                  book_authors: [],
                  book_tags: [],
                  book_categories: []
                })
              }
            >
              Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
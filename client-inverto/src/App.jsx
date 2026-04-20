import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import "./App.css";
import booksData from "./books.json";

const API_BASE = "http://localhost:8000";

const MOCK_AUTOCOMPLETE = [
  { id: 5, title: "Mastering Database Systems and Query Optimization Techniques", authors: ["Jennifer Widom"], publisher: "DataPress", edition: "2nd", publication_year: 2021 },
  { id: 1, title: "Introduction to Algorithms", authors: ["Thomas H. Cormen"], publisher: "MIT Press", edition: "4th", publication_year: 2022 },
  { id: 2, title: "Database System Concepts", authors: ["Abraham Silberschatz"], publisher: "McGraw-Hill", edition: "7th", publication_year: 2019 },
  { id: 3, title: "Clean Code: A Handbook of Agile Software Craftsmanship", authors: ["Robert C. Martin"], publisher: "Prentice Hall", edition: "1st", publication_year: 2008 },
  { id: 4, title: "Designing Data-Intensive Applications", authors: ["Martin Kleppmann"], publisher: "O'Reilly Media", edition: "1st", publication_year: 2017 },
];

// Parse books.json to extract unique publishers and categories
const extractFilterOptions = () => {
  const publishers = [...new Set(booksData.map(b => b.publisher))].sort();
  const categories = [...new Set(booksData.flatMap(b => b.categories || []))].sort();
  const languages = [...new Set(booksData.map(b => b.language))].sort();
  const years = [...new Set(booksData.map(b => b.publication_year))].sort((a, b) => b - a);
  
  return {
    publishers,
    categories,
    languages,
    years
  };
};

const MOCK_BOOK = {
  id: 5,
  title: "Mastering Database Systems and Query Optimization Techniques",
  description: "This book provides a deep understanding of database systems and how to optimize queries for performance. It begins with relational models and SQL fundamentals before diving into indexing, query planning, and execution. The book explains how databases use B-trees, hash indexes, and other structures internally. It also explores transaction management, ACID properties, and concurrency control mechanisms. Readers will learn how query optimizers work and how to write efficient queries. The book covers both relational and NoSQL systems, highlighting their differences and use cases. It also discusses distributed databases and replication strategies. Practical examples show how to diagnose slow queries and improve performance. By the end, readers will have a strong grasp of how databases operate internally and how to optimize them effectively.",
  publisher: "DataPress",
  publication_year: 2021,
  edition: "2nd",
  language: "English",
  authors: ["Jennifer Widom"],
  categories: ["Databases"],
  tags: ["sql", "optimization", "indexing"],
  pages: 780,
  isbn: "9780000000005",
};

function BookIcon({ size = 40, color = "#a78bfa" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="4" width="22" height="32" rx="3" fill={color} fillOpacity="0.15" stroke={color} strokeWidth="1.5" />
      <rect x="10" y="4" width="4" height="32" rx="2" fill={color} fillOpacity="0.3" />
      <line x1="14" y1="12" x2="24" y2="12" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="14" y1="17" x2="24" y2="17" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="14" y1="22" x2="20" y2="22" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="31" cy="31" r="7" fill={color} fillOpacity="0.2" stroke={color} strokeWidth="1.5" />
      <path d="M28 31l2 2 4-4" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function BookIconLarge() {
  return (
    <svg width="90" height="110" viewBox="0 0 90 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bookGradLarge" x1="12" y1="6" x2="72" y2="98" gradientUnits="userSpaceOnUse">
          <stop stopColor="#a78bfa" />
          <stop offset="1" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      <rect x="12" y="6" width="60" height="92" rx="6" fill="url(#bookGradLarge)" fillOpacity="0.18" stroke="url(#bookGradLarge)" strokeWidth="2" />
      <rect x="12" y="6" width="14" height="92" rx="4" fill="url(#bookGradLarge)" fillOpacity="0.35" />
      <line x1="32" y1="28" x2="62" y2="28" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" />
      <line x1="32" y1="40" x2="62" y2="40" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" />
      <line x1="32" y1="52" x2="62" y2="52" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" />
      <line x1="32" y1="64" x2="50" y2="64" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function Navbar({ onAddClick }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <div className="brand-icon">...</div>
          <span className="brand-name">Inverto</span>
        </div>

        <div className="navbar-links">
          <a href="#">Explore</a>
          <a href="#">Collections</a>
          <a href="#">About</a>

          <button className="add-book-btn" onClick={onAddClick}>
            + Add Book
          </button>
        </div>
      </div>
    </nav>
  );
}

function AutocompleteItem({ book, onSelect }) {
  return (
    <div className="autocomplete-item" onClick={() => onSelect(book)}>
      <div className="ac-icon"><BookIcon size={36} /></div>
      <div className="ac-info">
        <div className="ac-title">{book.title}</div>
        <div className="ac-meta">
          <span>{Array.isArray(book.authors) ? book.authors.join(", ") : book.authors}</span>
          <span className="dot">·</span>
          <span>{book.publisher}</span>
          <span className="dot">·</span>
          <span>{book.edition} ed.</span>
          <span className="dot">·</span>
          <span>{book.publication_year}</span>
        </div>
      </div>
    </div>
  );
}

function MetaCard({ label, value, icon }) {
  return (
    <div className="meta-card">
      <span className="meta-icon">{icon}</span>
      <div>
        <div className="meta-label">{label}</div>
        <div className="meta-value">{value}</div>
      </div>
    </div>
  );
}

function BookDetail({ book }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, [book?.id]);

  if (!book) return null;

  return (
    <div className={`book-detail ${visible ? "detail-visible" : ""}`}>
      <div className="detail-header">
        <div className="detail-icon"><BookIconLarge /></div>
        <div className="detail-title-block">
          <div className="detail-title">{book.title}</div>
          <div className="detail-authors">
            {(book.authors || []).map((a, i) => (
              <span key={i} className="author-chip">{a}</span>
            ))}
          </div>
          <div className="detail-publisher-row">
            <span className="pub-badge">{book.publisher}</span>
            <span className="edition-badge">{book.edition} Edition</span>
          </div>
        </div>
      </div>

      <div className="detail-divider" />

      <div className="detail-section">
        <div className="section-label">About this book</div>
        <p className="detail-description">{book.description}</p>
      </div>

      <div className="detail-divider" />

      <div className="detail-meta-grid">
        <MetaCard label="Publication Year" value={book.publication_year} icon="📅" />
        <MetaCard label="ISBN" value={book.isbn} icon="🔢" />
        <MetaCard label="Language" value={book.language} icon="🌐" />
        <MetaCard label="Pages" value={book.pages} icon="📄" />
      </div>

      <div className="detail-chips-row">
        <div className="chips-group">
          <span className="chips-label">Categories</span>
          <div className="chips">
            {(book.categories || []).map((c, i) => (
              <span key={i} className="chip chip-category">{c}</span>
            ))}
          </div>
        </div>
        <div className="chips-group">
          <span className="chips-label">Tags</span>
          <div className="chips">
            {(book.tags || []).map((t, i) => (
              <span key={i} className="chip chip-tag">#{t}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SearchResultsList({ results, onResultClick, loading }) {
  if (loading || results.length === 0) return null;

  return (
    <div className="search-results-container">
      <div className="results-header">{results.length} Results Found</div>
      <div className="results-list">
        {results.map((book) => (
          <div key={book.id} className="result-item" onClick={() => onResultClick(book)}>
            <div className="result-icon"><BookIcon size={32} /></div>
            <div className="result-content">
              <div className="result-title">{book.title}</div>
              <div className="result-meta">
                <span>{Array.isArray(book.authors) ? book.authors.join(", ") : book.authors}</span>
                <span className="dot">·</span>
                <span>{book.publisher}</span>
                <span className="dot">·</span>
                <span>{book.publication_year}</span>
              </div>
            </div>
            <div className="result-arrow">→</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [loading, setLoading] = useState(false);
  const [heroVisible, setHeroVisible] = useState(false);
  const debounceRef = useRef(null);
  const searchRef = useRef(null);
  const detailRef = useRef(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBook, setNewBook] = useState({
    title: "",
    description: "",
    publisher: "",
    publication_year: "",
    edition: "",
    language: "",
    authors: "",
    categories: "",
    tags: "",
    pages: "",
    isbn: ""
  });

  useEffect(() => {
    const t = setTimeout(() => setHeroVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const fetchSuggestions = useCallback(async (q) => {
    if (!q.trim()) { setSuggestions([]); return; }
    try {
      const res = await axios.post(`${API_BASE}/api/search/auto-complete`, { query: q });
      console.log('Auto-complete response:', res.data);
      let results = res.data;
      
      // Handle Elasticsearch hits format
      if (Array.isArray(results)) {
        results = results.map(hit => {
          const source = hit._source || hit;
          return {
            id: source.id || hit._id,
            title: source.title,
            authors: source.authors || [],
            publisher: source.publisher,
            edition: source.edition,
            publication_year: source.publication_year
          };
        });
      }
      
      setSuggestions(results || []);
    } catch (err) {
      console.error('Fetch error:', err);
      const filtered = MOCK_AUTOCOMPLETE.filter(b =>
        b.title.toLowerCase().includes(q.toLowerCase()) ||
        b.authors.some(a => a.toLowerCase().includes(q.toLowerCase()))
      );
      setSuggestions(filtered);
    }
  }, []);

  const handleInput = (e) => {
    const val = e.target.value;
    setQuery(val);
    setShowSuggestions(true);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 300);
  };

  const handleSelect = async (book) => {
    setShowSuggestions(false);
    setShowResults(false);
    setQuery(book.title);
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/api/book/${book.id}`);
      setSelectedBook(res.data);
    } catch {
      setSelectedBook(MOCK_BOOK);
    }
    setLoading(false);
    setTimeout(() => detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  };

  const handleKeyDown = async (e) => {
    if (e.key === "Enter" && query.trim()) {
      performSearch();
    }
  };

  const performSearch = async () => {
    if (!query.trim()) return;
    setShowSuggestions(false);
    setSelectedBook(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/search`, { query: query });
      console.log('Raw search response:', res.data);
      
      let results = [];
      
      // Handle different response formats
      if (Array.isArray(res.data)) {
        // Direct array of results
        results = res.data;
      } else if (res.data?.hits?.hits) {
        // Elasticsearch format with hits wrapper
        results = res.data.hits.hits;
      } else if (res.data?.results) {
        // Results wrapped in results property
        results = res.data.results;
      } else if (res.data?._source) {
        // Single result object
        results = [res.data];
      } else if (typeof res.data === 'object' && Object.keys(res.data).length > 0) {
        // Assume it's an array-like object
        results = Object.values(res.data);
      }
      
      console.log('Parsed results:', results);
      
      // Parse results if they have _source format (Elasticsearch)
      let parsedResults = results;
      if (Array.isArray(results) && results.length > 0) {
        if (results[0]._source) {
          // Elasticsearch hits format
          parsedResults = results.map(hit => ({
            id: hit._source.id || hit._id,
            title: hit._source.title,
            authors: hit._source.authors || [],
            publisher: hit._source.publisher,
            edition: hit._source.edition,
            publication_year: hit._source.publication_year
          }));
        } else if (results[0].id || results[0].title) {
          // Already in the correct format
          parsedResults = results;
        }
      }
      
      console.log('Final parsed results:', parsedResults);
      setSearchResults(parsedResults);
      setShowResults(true);
    } catch (err) {
      console.error('Search error:', err);
      setShowResults(false);
    }
    setLoading(false);
  };

  const handleAddBook = async () => {
      try {
        const payload = {
          ...newBook,
          id: Math.floor(Math.random() * 100000), // if required
          authors: newBook.authors.split(",").map(a => a.trim()),
          categories: newBook.categories.split(",").map(c => c.trim()),
          tags: newBook.tags ? newBook.tags.split(",").map(t => t.trim()) : [],
          publication_year: newBook.publication_year
            ? Number(newBook.publication_year)
            : null,
          pages: newBook.pages ? Number(newBook.pages) : null
        };

        console.log("Sending:", payload);

        const res = await axios.post(
          "http://localhost:8000/api/book/create-book",
          payload
        );

        console.log("Response:", res.data);

        alert("Book added successfully!");

        setShowAddModal(false);

      } catch (err) {
        console.error(err);
        alert("Error adding book");
      }
    };

  return (
    <div className="app">
      <div className="bg-glow glow-1" />
      <div className="bg-glow glow-2" />
      <div className="bg-glow glow-3" />

      <Navbar onAddClick={() => setShowAddModal(true)} />

      <main className="main-content">
        <div className={`hero ${heroVisible ? "hero-visible" : ""}`}>
          <div className="hero-eyebrow">Campus Library Intelligence</div>
          <h1 className="hero-title">
            Find any resource,<br />
            <span className="hero-accent">instantly.</span>
          </h1>
          <p className="hero-sub">
            Search across thousands of books, journals, and resources with semantic precision.
          </p>
        </div>

        <div className={`search-container ${heroVisible ? "search-visible" : ""}`} ref={searchRef}>
          <div className="search-wrapper">
            <div className="search-icon-left">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="8.5" cy="8.5" r="5.5" stroke="#7c3aed" strokeWidth="1.8" />
                <path d="M13 13l4 4" stroke="#7c3aed" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <input
              className="search-input"
              type="text"
              placeholder="Search by title, author, ISBN…"
              value={query}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              onFocus={() => query && setShowSuggestions(true)}
              autoComplete="off"
            />
            {query && (
              <button className="search-clear" onClick={() => { setQuery(""); setSuggestions([]); setSelectedBook(null); setShowResults(false); }}>✕</button>
            )}
            <button 
              className="search-button" 
              onClick={performSearch}
              title="Search"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M8 16C12.4183 16 16 12.4183 16 8C16 3.58172 12.4183 0 8 0C3.58172 0 0 3.58172 0 8C0 12.4183 3.58172 16 8 16Z" stroke="#7c3aed" strokeWidth="1.5" fill="none" />
                <path d="M13 13l6 6" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          {showSuggestions && suggestions.length > 0 && (
            <div className="autocomplete-dropdown">
              {suggestions.map((book) => (
                <AutocompleteItem key={book.id} book={book} onSelect={handleSelect} />
              ))}
            </div>
          )}
        </div>

        {loading && (
          <div className="loading-row">
            <div className="spinner" />
            <span>Searching library…</span>
          </div>
        )}

        {showResults && !selectedBook && (
          <SearchResultsList results={searchResults} onResultClick={handleSelect} loading={loading} />
        )}

        {selectedBook && !loading && (
          <div ref={detailRef} className="detail-wrapper">
            <BookDetail book={selectedBook} />
          </div>
        )}

        {!selectedBook && !showResults && !loading && (
          <div className={`empty-state ${heroVisible ? "empty-visible" : ""}`}>
            <div className="empty-books">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="empty-book-card" style={{ animationDelay: `${i * 0.15 + 0.6}s` }}>
                  <BookIcon size={32} color={["#a78bfa", "#818cf8", "#6ee7b7"][i]} />
                  <div className="empty-lines">
                    <div className="empty-line" style={{ width: ["70%", "55%", "65%"][i] }} />
                    <div className="empty-line short" style={{ width: ["45%", "40%", "50%"][i] }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="empty-hint">Start typing to search the library catalogue</p>
          </div>
        )}

        {showAddModal && (
          <div className="modal-overlay">
            <div className="modal-container">

              {/* HEADER */}
              <div className="modal-header">
                <div>
                  <h2>Add New Book</h2>
                  <p>Fill in details to add a new book</p>
                </div>
                <button onClick={() => setShowAddModal(false)}>✕</button>
              </div>

              {/* FORM */}
              <div className="modal-form">

                <div className="form-group">
                  <label>Title</label>
                  <input placeholder="Enter book title"
                    onChange={(e) => setNewBook({...newBook, title: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea placeholder="Enter description"
                    onChange={(e) => setNewBook({...newBook, description: e.target.value})}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Publisher</label>
                    <input
                      onChange={(e) => setNewBook({...newBook, publisher: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Year</label>
                    <input type="number"
                      onChange={(e) => setNewBook({...newBook, publication_year: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Edition</label>
                    <input
                      onChange={(e) => setNewBook({...newBook, edition: e.target.value})}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Language</label>
                    <input
                      onChange={(e) => setNewBook({...newBook, language: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Pages</label>
                    <input type="number"
                      onChange={(e) => setNewBook({...newBook, pages: e.target.value})}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>ISBN</label>
                  <input
                    onChange={(e) => setNewBook({...newBook, isbn: e.target.value})}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Authors</label>
                    <input placeholder="comma separated"
                      onChange={(e) => setNewBook({...newBook, authors: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Categories</label>
                    <input placeholder="comma separated"
                      onChange={(e) => setNewBook({...newBook, categories: e.target.value})}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Tags</label>
                  <input placeholder="comma separated"
                    onChange={(e) => setNewBook({...newBook, tags: e.target.value})}
                  />
                </div>

              </div>

              {/* ACTIONS */}
              <div className="modal-actions">
                <button className="btn cancel" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>

                <button
                  className="btn primary"
                  onClick={
                    handleAddBook
                  }
                >
                  Add Book
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

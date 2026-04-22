import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import "./App.css";
import { InsertBook } from "./InsertBook";

const API_BASE = import.meta.env.VITE_API_BASE || "";

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

function Navbar({ currentPage, onPageChange }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <div className="brand-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <defs>
                <linearGradient id="navGrad" x1="0" y1="0" x2="32" y2="32">
                  <stop stopColor="#7c3aed" />
                  <stop offset="1" stopColor="#4f46e5" />
                </linearGradient>
              </defs>
              <rect width="32" height="32" rx="8" fill="url(#navGrad)" />
              <path d="M8 24V10l6-3 6 3 6-3v14l-6 3-6-3-6 3z" stroke="white" strokeWidth="1.5" fill="none" strokeLinejoin="round" />
              <path d="M14 7v14M20 10v14" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <span className="brand-name">Inverto</span>
        </div>
        <div className="navbar-links">
          <button 
            className={`nav-link ${currentPage === 'search' ? 'active' : ''}`}
            onClick={() => onPageChange('search')}
          >
            Explore
          </button>
          <button 
            className={`nav-link ${currentPage === 'insert' ? 'active' : ''}`}
            onClick={() => onPageChange('insert')}
          >
            Add Book
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

function FilterModal({ isOpen, onClose, onApply, filterOptions }) {
  const [tempFilters, setTempFilters] = useState({
    author: "",
    publisher: "",
    category: "",
    language: ""
  });

  const handleFilterChange = (filterKey, value) => {
    setTempFilters(prev => ({
      ...prev,
      [filterKey]: value
    }));
  };

  const handleApply = () => {
    onApply(tempFilters);
    onClose();
  };

  const handleReset = () => {
    setTempFilters({
      author: "",
      publisher: "",
      category: "",
      language: ""
    });
  };

  if (!isOpen) return null;

  return (
    <div className="filter-modal-overlay" onClick={onClose}>
      <div className="filter-modal" onClick={(e) => e.stopPropagation()}>
        <div className="filter-modal-header">
          <h2>Filter Results</h2>
          <button className="filter-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="filter-modal-content">
          <div className="filter-group">
            <label>Authors</label>
            <select 
              value={tempFilters.author} 
              onChange={(e) => handleFilterChange("author", e.target.value)}
              className="filter-select"
            >
              <option value="">All Authors</option>
              {filterOptions.authors.map((author, idx) => (
                <option key={idx} value={author}>{author}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Publishers</label>
            <select 
              value={tempFilters.publisher} 
              onChange={(e) => handleFilterChange("publisher", e.target.value)}
              className="filter-select"
            >
              <option value="">All Publishers</option>
              {filterOptions.publishers.map((pub, idx) => (
                <option key={idx} value={pub}>{pub}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Categories</label>
            <select 
              value={tempFilters.category} 
              onChange={(e) => handleFilterChange("category", e.target.value)}
              className="filter-select"
            >
              <option value="">All Categories</option>
              {filterOptions.categories.map((cat, idx) => (
                <option key={idx} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Languages</label>
            <select 
              value={tempFilters.language} 
              onChange={(e) => handleFilterChange("language", e.target.value)}
              className="filter-select"
            >
              <option value="">All Languages</option>
              {filterOptions.languages.map((lang, idx) => (
                <option key={idx} value={lang}>{lang}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="filter-modal-footer">
          <button className="filter-btn-reset" onClick={handleReset}>Reset</button>
          <button className="filter-btn-apply" onClick={handleApply}>Apply Filters</button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [currentPage, setCurrentPage] = useState("search");
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [loading, setLoading] = useState(false);
  const [heroVisible, setHeroVisible] = useState(false);
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState({
    author: "",
    publisher: "",
    category: "",
    language: "",
    year_gte: "",
    year_lte: ""
  });
  const [filterOptions, setFilterOptions] = useState({
    authors: [],
    publishers: [],
    categories: [],
    languages: []
  });
  const debounceRef = useRef(null);
  const searchRef = useRef(null);
  const detailRef = useRef(null);

  // Fetch filter options from API on component mount
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/search/filters/options`);
        setFilterOptions(res.data);
      } catch (err) {
        console.error('Error fetching filter options:', err);
        // Fallback to empty filter options if API fails
        setFilterOptions({
          authors: [],
          publishers: [],
          categories: [],
          languages: []
        });
      }
    };
    fetchFilterOptions();
  }, []);

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
      // Build filters object excluding empty values
      const filters = {};
      if (selectedFilters.author) filters.author = selectedFilters.author;
      if (selectedFilters.publisher) filters.publisher = selectedFilters.publisher;
      if (selectedFilters.category) filters.category = selectedFilters.category;
      if (selectedFilters.language) filters.language = selectedFilters.language;
      if (selectedFilters.year_gte) filters.year_gte = parseInt(selectedFilters.year_gte);
      if (selectedFilters.year_lte) filters.year_lte = parseInt(selectedFilters.year_lte);

      const res = await axios.post(`${API_BASE}/api/search/auto-complete`, { 
        query: q,
        filters: filters 
      });
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
      // No fallback - just show empty suggestions on error
      setSuggestions([]);
    }
  }, [selectedFilters]);

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
    } catch (err) {
      console.error('Error fetching book details:', err);
      // Don't set selectedBook on error - let the user see the error in the UI
      setSelectedBook(null);
    }
    setLoading(false);
    setTimeout(() => detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  };

  const handleKeyDown = async (e) => {
    if (e.key === "Enter" && query.trim()) {
      performSearch();
    }
  };

  const handleApplyFilters = (filters) => {
    setSelectedFilters(filters);
  };

  const performSearch = async () => {
    if (!query.trim()) return;
    setShowSuggestions(false);
    setSelectedBook(null);
    setLoading(true);
    
    // Build filters object excluding empty values
    const filters = {};
    if (selectedFilters.author) filters.author = selectedFilters.author;
    if (selectedFilters.publisher) filters.publisher = selectedFilters.publisher;
    if (selectedFilters.category) filters.category = selectedFilters.category;
    if (selectedFilters.language) filters.language = selectedFilters.language;
    if (selectedFilters.year_gte) filters.year_gte = parseInt(selectedFilters.year_gte);
    if (selectedFilters.year_lte) filters.year_lte = parseInt(selectedFilters.year_lte);

    console.log('Filters being sent from frontend:', filters);

    try {
      const requestPayload = {
        query: query,
        filters: filters
      };
      
      console.log('Complete request payload:', requestPayload);
      
      const res = await axios.post(`${API_BASE}/api/search/`, requestPayload);
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

  return (
    <div className="app">
      <div className="bg-glow glow-1" />
      <div className="bg-glow glow-2" />
      <div className="bg-glow glow-3" />

      <Navbar currentPage={currentPage} onPageChange={setCurrentPage} />

      {currentPage === "search" && (
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
              className="filter-button" 
              onClick={() => setShowFilterModal(true)}
              title="Filters"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <line x1="2" y1="4" x2="18" y2="4" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="4" y1="10" x2="16" y2="10" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="7" y1="16" x2="13" y2="16" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
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
      </main>
      )}

      {currentPage === "insert" && (
        <div className="main-content">
          <InsertBook />
        </div>
      )}

      <FilterModal 
        isOpen={showFilterModal}
        onClose={() => setShowFilterModal(false)}
        onApply={handleApplyFilters}
        filterOptions={filterOptions}
      />
    </div>
  );
}

export default App;

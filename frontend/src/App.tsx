import {
  fetchImages,
  uploadImage,
  type UploadedImage,
  type ImageLibraryResponse,
} from './services/imageService'
import { useEffect, useRef, useState } from 'react'
import {
  ArrowDownRight,
  ArrowRight,
  AudioLines,
  Compass,
  Heart,
  ImagePlus,
  LayoutGrid,
  Search,
  Sparkles,
  WandSparkles,
} from 'lucide-react'
import './App.css'

const discoveries = [
  {
    title: 'Quiet moments',
    subtitle: 'Soft light, slow days',
    mood: 'SERENITY',
    image:
      'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?auto=format&fit=crop&w=900&q=85',
    className: 'discovery-tall',
  },
  {
    title: 'Somewhere in bloom',
    subtitle: 'Little things that feel like spring',
    mood: 'GENTLE',
    image:
      'https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=85',
    className: '',
  },
  {
    title: 'Blue hour',
    subtitle: 'The world, just before night',
    mood: 'DREAMY',
    image:
      'https://images.unsplash.com/photo-1472120435266-53107fd0c44a?auto=format&fit=crop&w=900&q=85',
    className: '',
  },
  {
    title: 'A little nostalgia',
    subtitle: 'Places that stay with us',
    mood: 'NOSTALGIC',
    image:
      'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=85',
    className: '',
  },
]

function App() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadedImages, setUploadedImages] = useState<
    ImageLibraryResponse['images']
  >([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadMessage, setUploadMessage] = useState('')
  const [query, setQuery] = useState('')
  const [activeNav, setActiveNav] = useState('Discover')
  const [saved, setSaved] = useState<string[]>([])

  useEffect(() => {
    let cancelled = false

    async function loadImages() {
      try {
        const result = await fetchImages()

        if (!cancelled) {
          setUploadedImages(result.images)
        }
      } catch (error) {
        console.error('Failed to load image library:', error)
      }
    }

    void loadImages()

    return () => {
      cancelled = true
    }
  }, [])

  function handleSearch() {
    if (!query.trim()) return
    window.alert(
      'Eloura search will be connected to the AI retrieval engine in a later milestone. Your search: ' +
      query,
    )
  }
  async function handleImageSelection(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]

    // Allow selecting the same image again later.
    event.target.value = ''

    if (!file) return

    setUploadError('')
    setUploadMessage('')

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setUploadError('Please select a JPEG, PNG, or WEBP image.')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('Your image must be 10 MB or smaller.')
      return
    }

    setUploading(true)

    try {

      await uploadImage(file)

      const result = await fetchImages()
      setUploadedImages(result.images)

      setActiveNav('My library')
      setUploadMessage('Your memory has been uploaded successfully.')

    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : 'Image upload failed.',
      )
    } finally {
      setUploading(false)
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setActiveNav('Discover')}>
          <span className="brand-symbol">e.</span>
          <span className="brand-name">eloura</span>
        </a>

        <div className="sidebar-label">YOUR SPACE</div>

        <nav className="main-nav" aria-label="Main navigation">
          <button
            className={`nav-item ${activeNav === 'Discover' ? 'active' : ''}`}
            onClick={() => setActiveNav('Discover')}
          >
            <Compass size={18} strokeWidth={1.7} />
            <span>Discover</span>
          </button>
          <button
            className={`nav-item ${activeNav === 'My library' ? 'active' : ''}`}
            onClick={() => setActiveNav('My library')}
          >
            <LayoutGrid size={18} strokeWidth={1.7} />
            <span>My library</span>
          </button>
          <button
            className={`nav-item ${activeNav === 'Mood boards' ? 'active' : ''}`}
            onClick={() => setActiveNav('Mood boards')}
          >
            <WandSparkles size={18} strokeWidth={1.7} />
            <span>Mood boards</span>
          </button>
        </nav>

        <div className="sidebar-note">
          <div className="note-icon">
            <Sparkles size={17} />
          </div>
          <p className="note-title">A space for your memories.</p>
          <p className="note-copy">
            Find the moments you remember, and the ones you almost forgot.
          </p>
        </div>

        <div className="sidebar-footer">
          <span className="status-dot" />
          <span>Your personal visual space</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <span className="breadcrumb">Your world, in pictures</span>
          <div className="upload-control">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              onChange={handleImageSelection}
            />

            <button
              className="upload-button"
              type="button"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
            >
              <ImagePlus size={17} />
              <span>{uploading ? 'Uploading...' : 'Add memories'}</span>
            </button>
          </div>
        </header>
        {uploadError && (
          <div className="upload-feedback upload-error" role="alert">
            {uploadError}
          </div>
        )}

        {uploadMessage && (
          <div className="upload-feedback upload-success" role="status">
            {uploadMessage}
          </div>
        )}
        <section className="hero">
          <div className="eyebrow">
            <span className="eyebrow-line" />
            YOUR VISUAL MEMORY
          </div>

          <h1>
            Some things are
            <br />
            <span>felt, not filed.</span>
          </h1>

          <p className="hero-description">
            Find a photograph by remembering how it felt.
            <br className="desktop-break" />
            A color, a place, a fleeting little moment.
          </p>

          <form
            className="search-box"
            onSubmit={(event) => {
              event.preventDefault()
              handleSearch()
            }}
          >
            <Search size={21} strokeWidth={1.7} className="search-icon" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="A rainy evening with golden lights..."
              aria-label="Describe a photograph to search for"
            />
            <button
              className="voice-button"
              type="button"
              aria-label="Voice search coming soon"
              title="Voice search coming soon"
              onClick={() =>
                window.alert('Voice search will be added in a future milestone.')
              }
            >
              <AudioLines size={20} />
            </button>
            <button className="search-submit" type="submit" aria-label="Search memories">
              <ArrowRight size={19} />
            </button>
          </form>

          <div className="search-hint">
            <Sparkles size={14} />
            <span>Search by feeling, color, place, or the smallest detail</span>
          </div>
        </section>

        <section className="discovery-section">
          <div className="section-heading">
            <div>
              <div className="section-kicker">A MOMENT TO YOURSELF</div>
              <h2>{activeNav === 'Discover' ? 'Explore a feeling' : activeNav}</h2>
            </div>
            <button
              className="text-link"
              onClick={() => setActiveNav('My library')}
            >
              <span>View your space</span>
              <ArrowDownRight size={17} />
            </button>
          </div>

          {activeNav === 'My library' && (
            <section className="library-section">
              <div className="library-intro">
                <ImagePlus size={20} />
                <div>
                  <strong>Your visual memories</strong>
                  <p>
                    {uploadedImages.length} image
                    {uploadedImages.length === 1 ? '' : 's'} uploaded in this session.
                  </p>
                </div>
              </div>

              {uploadedImages.length === 0 ? (
                <div className="library-empty">
                  <ImagePlus size={30} />
                  <h3>Your library begins with a memory.</h3>
                  <p>Upload an image to see it here.</p>
                  <button
                    className="upload-button"
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <ImagePlus size={16} />
                    Add your first image
                  </button>
                </div>
              ) : (
                <div className="uploaded-grid">
                  {uploadedImages.map((image) => (
                    <article className="uploaded-card" key={image.id}>
                      <img
                        src={`http://localhost:8000${image.url}`}
                        alt={image.filename}
                        loading="lazy"
                      />
                      <div className="uploaded-caption">
                        <strong title={image.filename}>{image.filename}</strong>
                        <span>
                          {image.width} × {image.height} · {image.format}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}

          {activeNav === 'Mood boards' && (
            <div className="library-notice">
              <WandSparkles size={19} />
              <div>
                <strong>Collect a feeling, create a world.</strong>
                <p>Your editable, personalized mood boards will be built after image retrieval.</p>
              </div>
            </div>
          )}

          <div className="discovery-grid">
            {discoveries.map((item) => {
              const isSaved = saved.includes(item.title)

              return (
                <article className={`discovery-card ${item.className}`} key={item.title}>
                  <img src={item.image} alt={item.title} loading="lazy" />
                  <div className="image-overlay" />
                  <span className="mood-tag">{item.mood}</span>
                  <button
                    className={`save-button ${isSaved ? 'saved' : ''}`}
                    aria-label={isSaved ? `Unsave ${item.title}` : `Save ${item.title}`}
                    aria-pressed={isSaved}
                    onClick={() =>
                      setSaved((current) =>
                        isSaved
                          ? current.filter((title) => title !== item.title)
                          : [...current, item.title],
                      )
                    }
                  >
                    <Heart size={17} fill={isSaved ? 'currentColor' : 'none'} />
                  </button>
                  <div className="card-caption">
                    <h3>{item.title}</h3>
                    <p>{item.subtitle}</p>
                  </div>
                </article>
              )
            })}
          </div>
          <p className="demo-caption">
            A little inspiration for now · Sample photography, not your personal memories
          </p>
        </section>

        <section className="closing-note">
          <div className="closing-icon">
            <Sparkles size={19} />
          </div>
          <div>
            <p className="closing-title">Every picture holds a feeling.</p>
            <p className="closing-copy">
              Eloura helps you find your way back to it.
            </p>
          </div>
          <ArrowDownRight className="closing-arrow" size={22} />
        </section>

        <footer className="page-footer">
          <span>eloura © 2026</span>
          <span>Made for the moments that matter.</span>
        </footer>
      </main>
    </div>
  )
}

export default App

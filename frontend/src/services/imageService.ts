
const API_BASE_URL = 'http://127.0.0.1:8001/api/v1'

export interface UploadedImage {
    id: string
    filename: string
    stored_filename: string
    format: string
    width: number
    height: number
    size_bytes: number
    status: string
}

export interface LibraryImage extends UploadedImage {
    created_at: string
    url: string
}

export async function uploadImage(file: File): Promise<UploadedImage> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/images/upload`, {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        const error = await response.json().catch(() => null)
        throw new Error(error?.detail ?? 'Unable to upload image.')
    }

    return response.json() as Promise<UploadedImage>
}

export interface ImageLibraryResponse {
    total: number
    images: LibraryImage[]
}

export async function fetchImages(): Promise<ImageLibraryResponse> {
    const response = await fetch(`${API_BASE_URL}/images`)

    if (!response.ok) {
        throw new Error('Unable to load your image library.')
    }

    return response.json() as Promise<ImageLibraryResponse>
}

export interface ImageSearchResult {
    id: string
    filename: string
    stored_filename: string
    url: string
    similarity: number
}

export interface ImageSearchResponse {
    query: string
    total: number
    results: ImageSearchResult[]
}

export async function searchImages(
    query: string,
    limit: number = 20,
): Promise<ImageSearchResponse> {
    const params = new URLSearchParams({
        query,
        limit: String(limit),
    })

    const response = await fetch(
        `${API_BASE_URL}/images/search?${params.toString()}`,
    )

    if (!response.ok) {
        const error = await response.json().catch(() => null)
        throw new Error(error?.detail ?? 'Unable to search your images.')
    }

    return response.json() as Promise<ImageSearchResponse>
}

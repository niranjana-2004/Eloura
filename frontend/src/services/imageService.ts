
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

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
    images: (UploadedImage & {
        created_at: string
        url: string
    })[]
}

export async function fetchImages(): Promise<ImageLibraryResponse> {
    const response = await fetch(`${API_BASE_URL}/images`)

    if (!response.ok) {
        throw new Error('Unable to load your image library.')
    }

    return response.json() as Promise<ImageLibraryResponse>
}

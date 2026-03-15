import React, { useCallback, useState } from 'react'
import { Upload, X, Image } from 'lucide-react'

const MAX_FILES = 2
const MAX_MB = 10
const ALLOWED = ['image/jpeg', 'image/png', 'image/heic', 'image/heif']

export default function PhotoUpload({ files, onChange }) {
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')

  const validate = (file) => {
    if (!ALLOWED.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|heic|heif)$/i)) {
      return 'Only JPG, PNG, HEIC files are allowed'
    }
    if (file.size > MAX_MB * 1024 * 1024) return `File too large (max ${MAX_MB} MB)`
    return null
  }

  const addFiles = useCallback((newFiles) => {
    setError('')
    const remaining = MAX_FILES - files.length
    if (remaining <= 0) { setError(`Maximum ${MAX_FILES} photos allowed`); return }
    const toAdd = Array.from(newFiles).slice(0, remaining)
    const errors = toAdd.map(validate).filter(Boolean)
    if (errors.length) { setError(errors[0]); return }
    onChange([...files, ...toAdd])
  }, [files, onChange])

  const remove = (idx) => onChange(files.filter((_, i) => i !== idx))

  const onDrop = (e) => {
    e.preventDefault(); setDragOver(false)
    addFiles(e.dataTransfer.files)
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
          dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-300'
        } ${files.length >= MAX_FILES ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}`}
        onClick={() => { if (files.length < MAX_FILES) document.getElementById('photo-input').click() }}
      >
        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600">
          {files.length >= MAX_FILES
            ? 'Maximum photos reached'
            : 'Drag & drop photos here, or click to select'}
        </p>
        <p className="text-xs text-gray-400 mt-1">JPG, PNG, HEIC · max {MAX_MB} MB · up to {MAX_FILES} photos</p>
        <input
          id="photo-input"
          type="file"
          accept=".jpg,.jpeg,.png,.heic,.heif"
          multiple
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {files.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-3">
          {files.map((file, idx) => (
            <div key={idx} className="relative rounded-lg overflow-hidden bg-gray-100 aspect-video">
              <img
                src={URL.createObjectURL(file)}
                alt=""
                className="w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); remove(idx) }}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center hover:bg-red-600"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

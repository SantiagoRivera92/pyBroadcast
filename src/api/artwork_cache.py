import requests
from pathlib import Path

class ArtworkCache:
    def __init__(self, cache_dir="cache/artworks"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cache_path(self, artwork_id):
        """Generate absolute cache file path for an artwork ID"""
        # Use artwork_id as filename to avoid collisions
        safe_id = str(artwork_id).replace('/', '_').replace('\\', '_')
        return (self.cache_dir / f"{safe_id}.jpg").resolve()
    
    def is_cached(self, artwork_id):
        """Check if artwork is already cached"""
        if not artwork_id:
            return False
        cache_path = self.get_cache_path(artwork_id)
        return cache_path and cache_path.exists()
    
    def get_cached_url(self, artwork_id):
        """Get file:// URL for cached artwork"""
        if not artwork_id:
            return None
        cache_path = self.get_cache_path(artwork_id)
        if cache_path and cache_path.exists():
            return cache_path.as_uri()
        return None
    
    def download_and_cache(self, artwork_url, artwork_id):
        """Download artwork and save to cache"""
        if not artwork_url or not artwork_id:
            return None
        
        cache_path = self.get_cache_path(artwork_id)
        
        # If already cached, return the path
        if cache_path.exists():
            return cache_path.as_uri()
        
        try:
            # Download the image
            response = requests.get(artwork_url, timeout=10)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            return cache_path.as_uri()
        except Exception as e:
            return artwork_url
    
    def clear_cache(self):
        """Clear all cached artworks"""
        for file in self.cache_dir.glob("*.jpg"):
            try:
                file.unlink()
            except Exception as e:
                pass
    
    def get_cache_size(self):
        """Get total size of cache in bytes"""
        total_size = 0
        for file in self.cache_dir.glob("*.jpg"):
            total_size += file.stat().st_size
        return total_size
    
    def get_cache_count(self):
        """Get number of cached artworks"""
        return len(list(self.cache_dir.glob("*.jpg")))
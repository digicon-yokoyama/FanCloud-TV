"""
Mock streaming service for video platform development.
This will be replaced with actual streaming service (AWS IVS, Bitmovin, etc.)
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List


class MockStreamingService:
    """Mock streaming service that simulates video streaming platform capabilities."""
    
    def __init__(self):
        self.streams = {}
        self.recordings = {}
        
    def generate_stream_key(self) -> str:
        """Generate a unique stream key."""
        return f"mock_key_{uuid.uuid4().hex[:16]}"
    
    def generate_ingest_url(self, stream_key: str) -> str:
        """Generate RTMP ingest URL for streaming."""
        return f"rtmp://mock-ingest.streaming-platform.local/live/{stream_key}"
    
    def generate_playback_url(self, stream_id: str) -> str:
        """Generate HLS playback URL."""
        return f"https://mock-cdn.streaming-platform.local/{stream_id}.m3u8"
    
    def generate_thumbnail_url(self, stream_id: str) -> str:
        """Generate thumbnail image URL."""
        return f"https://mock-cdn.streaming-platform.local/{stream_id}/thumbnail.jpg"
    
    def create_stream(self, title: str, description: str = "") -> Dict[str, Any]:
        """Create a new live stream."""
        stream_id = str(uuid.uuid4())
        stream_key = self.generate_stream_key()
        
        stream_data = {
            'stream_id': stream_id,
            'stream_key': stream_key,
            'title': title,
            'description': description,
            'status': 'created',
            'ingest_url': self.generate_ingest_url(stream_key),
            'playback_url': self.generate_playback_url(stream_id),
            'thumbnail_url': self.generate_thumbnail_url(stream_id),
            'created_at': datetime.now().isoformat(),
            'viewer_count': 0,
            'is_recording': True,
        }
        
        self.streams[stream_id] = stream_data
        return stream_data
    
    def start_stream(self, stream_id: str) -> Dict[str, Any]:
        """Start streaming (simulate going live)."""
        if stream_id in self.streams:
            self.streams[stream_id]['status'] = 'live'
            self.streams[stream_id]['started_at'] = datetime.now().isoformat()
            self.streams[stream_id]['viewer_count'] = random.randint(1, 100)
            return self.streams[stream_id]
        return {'error': 'Stream not found'}
    
    def stop_stream(self, stream_id: str) -> Dict[str, Any]:
        """Stop streaming and create VOD recording."""
        if stream_id in self.streams:
            stream = self.streams[stream_id]
            stream['status'] = 'ended'
            stream['ended_at'] = datetime.now().isoformat()
            
            # Create VOD recording
            if stream['is_recording']:
                recording_id = str(uuid.uuid4())
                recording_data = {
                    'recording_id': recording_id,
                    'stream_id': stream_id,
                    'title': stream['title'] + ' (録画)',
                    'description': stream['description'],
                    'playback_url': f"https://mock-cdn.streaming-platform.local/vod/{recording_id}.m3u8",
                    'thumbnail_url': f"https://mock-cdn.streaming-platform.local/vod/{recording_id}/thumbnail.jpg",
                    'duration': random.randint(300, 7200),  # 5min to 2hours
                    'created_at': stream.get('started_at', datetime.now().isoformat()),
                    'file_size': random.randint(100, 2000) * 1024 * 1024,  # 100MB to 2GB
                    'status': 'ready'
                }
                self.recordings[recording_id] = recording_data
                stream['recording_id'] = recording_id
            
            return stream
        return {'error': 'Stream not found'}
    
    def get_stream_status(self, stream_id: str) -> Dict[str, Any]:
        """Get current stream status."""
        if stream_id in self.streams:
            stream = self.streams[stream_id].copy()
            if stream['status'] == 'live':
                # Simulate changing viewer count
                stream['viewer_count'] = random.randint(
                    max(1, stream['viewer_count'] - 10),
                    stream['viewer_count'] + 20
                )
                self.streams[stream_id]['viewer_count'] = stream['viewer_count']
            return stream
        return {'error': 'Stream not found'}
    
    def upload_vod(self, title: str, description: str = "", file_size: int = 0) -> Dict[str, Any]:
        """Simulate VOD file upload."""
        recording_id = str(uuid.uuid4())
        
        recording_data = {
            'recording_id': recording_id,
            'title': title,
            'description': description,
            'playback_url': f"https://mock-cdn.streaming-platform.local/vod/{recording_id}.m3u8",
            'thumbnail_url': f"https://mock-cdn.streaming-platform.local/vod/{recording_id}/thumbnail.jpg",
            'duration': random.randint(60, 3600),  # 1min to 1hour
            'created_at': datetime.now().isoformat(),
            'file_size': file_size or random.randint(50, 500) * 1024 * 1024,  # 50MB to 500MB
            'status': 'processing',
            'progress': 0
        }
        
        self.recordings[recording_id] = recording_data
        return recording_data
    
    def get_vod_status(self, recording_id: str) -> Dict[str, Any]:
        """Get VOD processing status."""
        if recording_id in self.recordings:
            recording = self.recordings[recording_id].copy()
            if recording['status'] == 'processing':
                # Simulate processing progress
                recording['progress'] = min(100, recording.get('progress', 0) + random.randint(5, 20))
                if recording['progress'] >= 100:
                    recording['status'] = 'ready'
                self.recordings[recording_id] = recording
            return recording
        return {'error': 'Recording not found'}
    
    def list_streams(self, status: str = None) -> List[Dict[str, Any]]:
        """List all streams, optionally filtered by status."""
        streams = list(self.streams.values())
        if status:
            streams = [s for s in streams if s['status'] == status]
        return sorted(streams, key=lambda x: x['created_at'], reverse=True)
    
    def list_recordings(self) -> List[Dict[str, Any]]:
        """List all VOD recordings."""
        return sorted(self.recordings.values(), key=lambda x: x['created_at'], reverse=True)
    
    def delete_stream(self, stream_id: str) -> bool:
        """Delete a stream."""
        if stream_id in self.streams:
            del self.streams[stream_id]
            return True
        return False
    
    def delete_recording(self, recording_id: str) -> bool:
        """Delete a VOD recording."""
        if recording_id in self.recordings:
            del self.recordings[recording_id]
            return True
        return False
    
    def get_analytics(self, stream_id: str = None, days: int = 7) -> Dict[str, Any]:
        """Get mock analytics data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_views': random.randint(100, 10000),
            'unique_viewers': random.randint(50, 5000),
            'total_watch_time': random.randint(1000, 100000),  # minutes
            'peak_concurrent_viewers': random.randint(10, 500),
            'average_watch_time': random.randint(5, 45),  # minutes
            'engagement_rate': round(random.uniform(0.1, 0.8), 2),
            'top_countries': [
                {'country': 'Japan', 'views': random.randint(100, 1000)},
                {'country': 'United States', 'views': random.randint(50, 500)},
                {'country': 'South Korea', 'views': random.randint(20, 200)},
            ]
        }
        
        if stream_id and stream_id in self.streams:
            analytics['stream_id'] = stream_id
        
        return analytics


# Global instance
mock_streaming_service = MockStreamingService()
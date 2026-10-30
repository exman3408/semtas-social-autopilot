"""Minimal Buffer GraphQL client, consistent with developers.buffer.com examples."""
import os
import requests

API = 'https://api.buffer.com'

class BufferError(RuntimeError):
    pass

class BufferAPI:
    def __init__(self, token=None):
        self.token = (token or os.getenv('BUFFER_API_KEY', '')).strip()
        if not self.token:
            raise BufferError('BUFFER_API_KEY gerekli')

    def call(self, query, variables=None):
        try:
            resp = requests.post(API,
                headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                json={'query': query, 'variables': variables or {}}, timeout=30)
            resp.raise_for_status()
            result = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise BufferError(f'Buffer HTTP/network hatası: {type(exc).__name__}') from exc
        if result.get('errors'):
            raise BufferError('Buffer GraphQL: ' + '; '.join(e.get('message', 'Hata') for e in result['errors'])[:300])
        return result.get('data', {})

    def organizations(self):
        result = self.call('query { account { organizations { id name } } }')
        return result['account']['organizations']

    def channels(self, org_id):
        # Scalar interpolated via JSON serializer prevents GraphQL injection.
        import json
        q = f'query {{ channels(input: {{ organizationId: {json.dumps(org_id)} }}) {{ id name service isQueuePaused isDisconnected isLocked }} }}'
        return self.call(q)['channels']

    def exists_matching_post(self, org_id, channel_id, caption):
        """Prevent duplicate queue submissions, checking multiple pages. Fail closed if incomplete."""
        import json
        cursor = None
        for _ in range(10):
            arg = f', after: {json.dumps(cursor)}' if cursor else ''
            q = ('query { posts(first: 50' + arg + ', input: {organizationId: ' + json.dumps(org_id) +
                 ', filter: {channelIds: [' + json.dumps(channel_id) + '], status: [scheduled, sent]}})'
                 ' { edges { node { id text channelId } } pageInfo { hasNextPage endCursor } } }')
            info = self.call(q)['posts']
            for edge in info.get('edges', []):
                node = edge['node']
                if node.get('channelId') == channel_id and node.get('text') == caption:
                    return node['id']
            page = info.get('pageInfo', {})
            if not page.get('hasNextPage'):
                return None
            cursor = page.get('endCursor')
            if not cursor:
                break
        raise BufferError('Buffer listesi çok uzun/eksik; iki kez paylaşmamak için durduruldu')

    def queue_image(self, channel_id, caption, image_url, due_at=None):
        q = '''mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            ... on PostActionSuccess { post { id dueAt } }
            ... on MutationError { message }
          }
        }'''
        inp = {
            'text': caption, 'channelId': channel_id, 'schedulingType': 'automatic',
            'mode': 'customScheduled' if due_at else 'addToQueue', 'aiAssisted': True,
            'assets': [{'image': {'url': image_url}}],
        }
        if due_at:
            inp['dueAt'] = due_at
        result = self.call(q, {'input': inp}).get('createPost', {})
        if result.get('message'):
            raise BufferError('Buffer gönderim hatası: ' + result['message'][:300])
        post = result.get('post')
        if not post or not post.get('id'):
            raise BufferError('Buffer beklenmeyen yanıt döndürdü')
        return post

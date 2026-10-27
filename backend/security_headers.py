"""Response safeguards for the bundled same-origin production frontend."""
class SecurityHeaders:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        async def protected(message):
            if message['type']=='http.response.start':
                headers=list(message.get('headers',[]))
                headers.extend([(b'x-content-type-options',b'nosniff'),(b'referrer-policy',b'no-referrer'),(b'x-frame-options',b'DENY'),(b'permissions-policy',b'camera=(), microphone=(), geolocation=()')])
                # API docs use their own external scripts; leave CSP for the actual app/pages.
                if scope.get('path') not in ('/docs','/redoc','/docs/oauth2-redirect'):
                    headers.append((b'content-security-policy',b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; frame-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"))
                message={**message,'headers':headers}
            await send(message)
        await self.app(scope,receive,protected)

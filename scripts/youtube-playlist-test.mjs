const playlistId = 'PLsSYtv-Nd6UgXJa462Phtz5C0rkM7zhOJ';
const videoId = process.env.YOUTUBE_VIDEO_ID ?? '';
if (!/^[\w-]{11}$/.test(videoId)) throw new Error('Enter an 11-character YouTube video ID.');
if (!process.env.YOUTUBE_OAUTH) throw new Error('Set the YOUTUBE_OAUTH Actions secret first.');
let credentials;
try {
  credentials = JSON.parse(process.env.YOUTUBE_OAUTH);
} catch {
  throw new Error('YOUTUBE_OAUTH must contain the local OAuth JSON.');
}
const { client_id, client_secret, refresh_token } = credentials;
if (!client_id || !client_secret || !refresh_token) throw new Error('OAuth fields are missing.');

const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
  method: 'POST',
  body: new URLSearchParams({ client_id, client_secret, refresh_token, grant_type: 'refresh_token' }),
  signal: AbortSignal.timeout(20000),
});
if (!tokenResponse.ok) throw new Error(`Google OAuth failed (HTTP ${tokenResponse.status}).`);
const { access_token } = await tokenResponse.json();
if (!access_token) throw new Error('Google did not return an access token.');

const response = await fetch('https://www.googleapis.com/youtube/v3/playlistItems?part=snippet', {
  method: 'POST',
  headers: { Authorization: `Bearer ${access_token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ snippet: { playlistId, resourceId: { kind: 'youtube#video', videoId } } }),
  signal: AbortSignal.timeout(20000),
});
if (!response.ok) throw new Error(`YouTube playlist insertion failed (HTTP ${response.status}).`);
const item = await response.json();
if (!item.id || item.snippet?.playlistId !== playlistId) throw new Error('YouTube did not confirm the target playlist.');
console.log(`Added video ${videoId} to Musical Number.`);

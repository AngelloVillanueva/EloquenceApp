/** Vertex shared by gold (ANIMATION_12) and night (ANIMATION_17) orbs. */
export const VERT = `
attribute vec2 a_position;
varying vec2 v_texCoord;
void main() {
  v_texCoord = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`

const SNOISE = `
vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw)), 0.0);
  m = m*m ;
  m = m*m ;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 a0 = x - floor(x + 0.5);
  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
`

/** Liquid gold — ElevateAI Desing/Orb 2 + gold standard ANIMATION_12. */
export const FRAG_GOLD = `
precision highp float;
varying vec2 v_texCoord;
uniform float u_time;
uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_intensity;
uniform float u_speed;
uniform float u_glow;
${SNOISE}
void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / min(u_resolution.x, u_resolution.y);
    float t = u_time * 0.5 * max(u_speed, 0.18);

    float noise1 = snoise(uv * 1.8 + t);
    float noise2 = snoise(uv * 3.5 - t * 0.7);
    float combinedNoise = noise1 * 0.6 + noise2 * 0.4;

    float radius = 0.40 + 0.08 * u_intensity + 0.12 * combinedNoise;
    float d = length(uv) - radius;

    vec3 colorGold = vec3(0.91, 0.66, 0.49);
    vec3 colorAmber = vec3(0.83, 0.53, 0.29);

    float core = (0.018 * u_glow) / abs(d + 0.015);
    vec3 finalColor = mix(colorGold, colorAmber, combinedNoise * 0.5 + 0.5) * core;

    float shimmer = pow(max(0.0, snoise(uv * 10.0 + t * 2.0)), 5.0);
    finalColor += colorGold * shimmer * 0.8 * u_intensity * smoothstep(0.1, -0.1, d);

    float bloom = smoothstep(0.8, 0.0, length(uv));
    finalColor += vec3(0.06, 0.05, 0.04) * bloom * u_glow;

    float grain = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
    finalColor += (grain - 0.5) * 0.02;

    gl_FragColor = vec4(finalColor, 1.0);
}`

/** Cream core + waveform rings — ElevateAI Desing/Obr Nightmode ANIMATION_17. */
export const FRAG_NIGHT = `
precision highp float;
varying vec2 v_texCoord;
uniform float u_time;
uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_intensity;
uniform float u_speed;
uniform float u_glow;
${SNOISE}
void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / min(u_resolution.x, u_resolution.y);
    float t = u_time * 1.2 * max(u_speed, 0.18);

    float n = snoise(uv * 1.5 + t * 0.4);
    float d = length(uv) - (0.36 + 0.08 * u_intensity + 0.10 * n);

    vec3 coreColor = vec3(1.0, 0.99, 0.98);
    vec3 bloomColor1 = vec3(0.88, 0.69, 0.50);
    vec3 bloomColor2 = vec3(0.78, 0.54, 0.29);

    float glow = (0.018 * u_glow) / abs(d + 0.015);
    vec3 finalColor = mix(bloomColor1, bloomColor2, n * 0.5 + 0.5) * glow;
    finalColor += coreColor * smoothstep(0.1, -0.1, d) * 0.8 * u_intensity;

    float angle = atan(uv.y, uv.x);
    float pulse = snoise(vec2(angle * 2.0, t * 2.0));
    float wave = 0.5 + 0.5 * sin(angle * 16.0 + t * 8.0) * pulse * u_intensity;
    float ringRadius = 0.52 + 0.05 * u_intensity + 0.04 * wave;
    float waveCircle = abs(length(uv) - ringRadius) - 0.002;
    finalColor += bloomColor1 * (0.002 / abs(waveCircle + 0.006)) * 0.55 * u_glow;

    float ambient = smoothstep(1.5, 0.0, length(uv));
    finalColor += vec3(0.1, 0.07, 0.05) * ambient * u_glow;

    float grain = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
    finalColor += (grain - 0.5) * 0.03;

    gl_FragColor = vec4(finalColor, 1.0);
}`

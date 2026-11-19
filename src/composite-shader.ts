// Blend complete scenes, including animated geometry outlines.
export const compositeFragment = `
uniform sampler2D a;
uniform sampler2D b;
uniform float mixValue;
varying vec2 uv0;
void main(){
 gl_FragColor=mix(texture2D(a,uv0),texture2D(b,uv0),mixValue);
 #include <colorspace_fragment>
}`;

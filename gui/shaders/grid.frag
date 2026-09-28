#version 330

in float v_dist;
out vec4 fragColor;

void main() {
    // Fade com a distância
    float alpha = max(0.0, 1.0 - v_dist / 12.0) * 0.35;
    fragColor = vec4(0.5, 0.5, 0.5, alpha);
}

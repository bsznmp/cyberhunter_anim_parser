#version 330

uniform int u_mode;  // 0=solid, 1=submesh, 2=weights

in vec3 v_normal;
in float v_submesh;
in float v_weight;

out vec4 fragColor;

vec3 submesh_palette(float t) {
    int idx = int(t * 7.0 + 0.5);
    if (idx == 0) return vec3(0.85, 0.35, 0.35);
    if (idx == 1) return vec3(0.35, 0.75, 0.35);
    if (idx == 2) return vec3(0.35, 0.55, 0.95);
    if (idx == 3) return vec3(0.95, 0.75, 0.25);
    if (idx == 4) return vec3(0.75, 0.35, 0.85);
    if (idx == 5) return vec3(0.35, 0.85, 0.85);
    if (idx == 6) return vec3(0.95, 0.55, 0.25);
    return vec3(0.70, 0.70, 0.70);
}

vec3 weight_heatmap(float t) {
    vec3 cold = vec3(0.1, 0.2, 0.8);
    vec3 mid  = vec3(0.1, 0.9, 0.1);
    vec3 hot  = vec3(0.9, 0.1, 0.1);
    if (t < 0.5) return mix(cold, mid, t * 2.0);
    return mix(mid, hot, (t - 0.5) * 2.0);
}

void main() {
    vec3 light_dir = normalize(vec3(0.3, 1.0, 0.5));
    vec3 norm = normalize(v_normal);

    float ambient = 0.15;
    float diffuse = max(dot(norm, light_dir), 0.0) * 0.65;
    float rim = pow(1.0 - max(dot(norm, vec3(0.0, 0.0, 1.0)), 0.0), 3.0) * 0.2;
    float intensity = ambient + diffuse + rim;

    vec3 color;
    if (u_mode == 1) {
        color = submesh_palette(v_submesh) * intensity;
    } else if (u_mode == 2) {
        color = weight_heatmap(v_weight);
    } else {
        color = vec3(0.72, 0.73, 0.78) * intensity;
    }

    fragColor = vec4(color, 1.0);
}

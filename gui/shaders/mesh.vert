#version 330

uniform mat4 mvp;
uniform mat3 normal_matrix;

in vec3 in_position;
in vec3 in_normal;
in float in_submesh;
in float in_weight;

out vec3 v_normal;
out float v_submesh;
out float v_weight;

void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    v_normal = normalize(normal_matrix * in_normal);
    v_submesh = in_submesh;
    v_weight = in_weight;
}

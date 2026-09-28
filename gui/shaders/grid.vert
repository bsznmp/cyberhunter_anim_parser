#version 330

uniform mat4 mvp;

in vec3 in_position;
out float v_dist;

void main() {
    gl_Position = mvp * vec4(in_position, 1.0);
    v_dist = length(in_position.xz);
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from kivy.uix.effectwidget import EffectWidget, EffectBase
from kivy.properties import NumericProperty


effect_alpha = '''
#ifdef GL_ES
precision mediump float;
#endif

vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{{
    float alpha;
    if (resolution.{1} - coords.{1} < {0})
    {{
        alpha = (resolution.{1} - coords.{1})/{0};
    }}
    else if (coords.{1} < {0})
    {{
        alpha = coords.{1}/{0};
    }}
    else
    {{
        alpha = 1.;
    }}

    return vec4(color.x, color.y, color.z, color.w*alpha);
}}
'''


class AlphaEffect(EffectBase):

    effect_width = NumericProperty()

    '''Fades the widget in and out at the borders.'''

    def __init__(self, effect_width=10, orientation='horizontal', *args, **kwargs):
        super(AlphaEffect, self).__init__(*args, **kwargs)
        self.effect_axis = 'x' if orientation == 'horizontal' else 'y'
        self.effect_width = effect_width

    def on_effect_width(self, *args):
        self.do_glsl()

    def do_glsl(self):
        print('Doing GLSL with {}'.format(self.effect_width, self.effect_axis))
        self.glsl = effect_alpha.format(self.effect_width/1.0, self.effect_axis)
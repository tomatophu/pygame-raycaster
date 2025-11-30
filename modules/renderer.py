import math
from numbers import Real
from typing import Self
from typing import Union
from threading import Thread
from collections.abc import Sequence

import numpy as np
import pygame as pg
from pygame.typing import Point

from modules.texture import WallTexture
from modules.texture import FloorTexture
from modules.entities import Player
from modules.entities import EntityManager


class Camera(object):
    def __init__(self: Self,
                 fov: Real,
                 tile_size: Real,
                 wall_render_distance: Real,
                 wall_textures: Sequence[WallTexture],
                 floor_texture: FloorTexture,
                 player: Player,
                 bob_strength: Real=0.075,
                 bob_frequency: Real=10) -> None:
        
        try:
            self._yaw_magnitude = float(1 / math.tan(math.radians(fov) / 2))
        except ValueError:
            self._yaw_magnitude = 0
        # already sets yaw V
        self.fov = min(abs(fov), 180) # _fov is in degrees
        self._horizon = None
        self._player = player
        self._tile_size = tile_size
        self._render_elevation = self._player._elevation
        self._wall_render_distance = wall_render_distance
        self._wall_textures = wall_textures
        self._floor_texture = floor_texture

        self.bob_strength = bob_strength
        self.bob_frequency = bob_frequency

    @property
    def bob_strength(self: Self) -> Real:
        return self._bob_stength

    @bob_strength.setter
    def bob_strength(self: Self, value: Real) -> None:
        value = pg.math.clamp(value, -0.5, 0.5)
        self._bob_strength = value
        self._player._settings['bob_strength'] = value

    @property
    def bob_frequency(self: Self) -> Real:
        return self._bob_frequency

    @bob_frequency.setter
    def bob_frequency(self: Self, value: Real) -> None:
        self._bob_frequency = value
        self._player._settings['bob_frequency'] = value

    @property
    def player(self: Self) -> Player:
        return self._player

    @player.setter
    def player(self: Self, value: Player) -> None:
        self._player._settings['bob_frequency'] = 0
        self._player._settings['bob_strength'] = 0
        self._player = value
        value._settings['bob_frequency'] = self._bob_frequency
        value._settings['bob_strength'] = self._bob_strength

    @property
    def fov(self: Self) -> Real:
        return self._fov

    @fov.setter
    def fov(self: Self, value: Real) -> None:
        self._fov = value
        try:
            self._yaw_magnitude = float(1 / math.tan(math.radians(value) / 2))
        except ValueError:
            self._yaw_magnitude = 0

    @property
    def horizon(self: Self) -> Real:
        if self._horizon == None:
            raise AttributeError('set a horizon first')
        return self._horizon

    @horizon.setter
    def horizon(self: Self, value: Real) -> None:
        self._horizon = value

    @property
    def tile_size(self: Self) -> Real:
        return self._tile_size

    @tile_size.setter
    def tile_size(self: Self, value: Real) -> None:
        self._tile_size = value

    @property
    def wall_render_distance(self: Self) -> Real:
        return self._wall_render_distance

    @wall_render_distance.setter
    def wall_render_distance(self: Self, value: Real) -> None:
        self._wall_render_distance = value

    def _render_floor_and_ceiling(self: Self,
                                  width: Real,
                                  height: Real,
                                  horizon: Real) -> None:

        # Floor Casting
        difference = int(height - horizon)
        amount_of_offsets = min(difference, height)
        self._floor_and_ceiling = 0 

        if difference >= 1:
            self._floor_and_ceiling = pg.Surface((width, amount_of_offsets))
            rays = (self._yaw - self._player._semiplane,
                    self._yaw + self._player._semiplane)
            x_pixels = np.linspace(0, width, num=width, endpoint=0) 
            x_pixels = np.vstack(x_pixels) # all x values
            offsets = np.linspace(
                max(-horizon, 1),
                amount_of_offsets + max(-horizon, 0),
                num=amount_of_offsets,
                endpoint=0
            ) # offsets from horizon to render
            
            # takes into account elevation
            # basically, some of the vertical camera plane is below the ground
            # intersection between ground and ray is behind the plane
            # (not in front); we use this multiplier
            mult = self._tile_size / 2 * (1 + self._player._render_elevation)
            start_points_x = mult / offsets * rays[0][0]
            start_points_y = mult / offsets * rays[0][1]

            end_points_x = mult / offsets * rays[1][0]
            end_points_y = mult / offsets * rays[1][1]

            step_x = (end_points_x - start_points_x) / width
            step_y = (end_points_y - start_points_y) / width
            
            x_points = self._player._pos.x + start_points_x + step_x * x_pixels
            y_points = self._player._pos.y + start_points_y + step_y * x_pixels
            
            texture = self._floor_texture
            # change the multiplier before the mod to change size of texture
            texture_xs = np.floor(x_points * 1 % 1 * texture.width)
            texture_ys = np.floor(y_points * 1 % 1 * texture.height)
            texture_xs = texture_xs.astype('int')
            texture_ys = texture_ys.astype('int')

            floor = texture[texture_xs, texture_ys]
            # lighting
            offsets = np.vstack(offsets)
            floor = floor * np.minimum(offsets / (height / 2), 1)**0.97
            # can't do *= ^
            pg.surfarray.blit_array(self._floor_and_ceiling, floor)

    def _render_walls_and_entities(self: Self,
                                   width: Real,
                                   height: Real,
                                   horizon: Real) -> None:
        # the per-pixel alpha with (0, 0, 0, 0) doesn't seem to affect
        # fps at all
        self._walls_and_entities = pg.Surface((width, height), pg.SRCALPHA)
        self._walls_and_entities.fill((0, 0, 0, 0))
        # Wall Casting
        for x in range(width):
            ray = self._yaw + self._player._semiplane * (2 * x / width - 1)
            mag = ray.magnitude()

            has_hit = 0
            end_pos = self._player._pos.copy()
            slope = ray.y / ray.x if ray.x else math.inf
            tile = pg.Vector2(math.floor(end_pos.x), math.floor(end_pos.y))
            dir = (ray.x > 0, ray.y > 0)
            depth = 0
            dist = 0 
            # keep on changing end_pos until hitting a wall (DDA)
            while not has_hit and dist < self._wall_render_distance:
                # displacements until hit tile
                disp_x = tile.x + dir[0] - end_pos.x
                disp_y = tile.y + dir[1] - end_pos.y
                # step for tile (for each displacement)
                step_x = dir[0] * 2 - 1 # 1 if yes, -1 if no
                step_y = dir[1] * 2 - 1 
                # relative lengths of each semiray
                len_x = abs(disp_x / ray.x) if ray.x else math.inf
                len_y = abs(disp_y / ray.y) if ray.y else math.inf
                if len_x < len_y:
                    tile.x += step_x
                    end_pos.x += disp_x
                    end_pos.y += disp_x * slope
                    depth += len_x
                    side = 1
                else:
                    tile.y += step_y
                    end_pos.x += disp_y / slope if slope else math.inf
                    end_pos.y += disp_y
                    depth += len_y
                    side = 0
                dist = depth * mag
                
                tile_key = f'{int(tile.x)};{int(tile.y)}'
                has_hit = (self._player._level['walls'].get(tile_key) != None 
                           and depth)
            if has_hit:
                # distance already does fisheye correction because it divides
                # by the magnitude of ray (when "depth" is 1)
                line_height = min(self._tile_size / depth, height * 5)
                # elevation offset
                offset = (self._player._render_elevation
                          * self._tile_size / 2 / depth)
                # check if line is visible
                if (-line_height / 2 - offset < horizon 
                    < height + line_height / 2 - offset):
                    texture = self._player._level['walls'][tile_key]
                    dex = math.floor(end_pos[side] % 1
                                     * self._wall_textures[texture].width)
                    line = pg.transform.scale(
                        self._wall_textures[texture][dex],
                        (1, line_height + 2)
                    )
                    # ^ +2 to avoid pixel glitches at edges of wall
                    pg.transform.hsl(line, 0, 0, max(-dist / 6, -1), line)

                    self._walls_and_entities.blit(
                        line, (x, horizon - line_height / 2 + offset),
                    )
    
    def render(self: Self, surf: pg.Surface) -> None:
        width = surf.width
        height = surf.height

        surf.fill((0, 0, 0))
        self._yaw = self._player._yaw * self._yaw_magnitude
 
        horizon = self._horizon
        if self._horizon == None:
            horizon = int(height / 2)

        floor_and_ceiling = Thread(
            target=self._render_floor_and_ceiling,
            args=(width, height, horizon),
        )
        walls_and_entities = Thread(
            target=self._render_walls_and_entities,
            args=(width, height, horizon),
        )
        floor_and_ceiling.start()
        walls_and_entities.start()
        floor_and_ceiling.join()
        walls_and_entities.join()

        if self._floor_and_ceiling:
            surf.blit(self._floor_and_ceiling, (0, max(0, horizon)))
        surf.blit(self._walls_and_entities, (0, 0))


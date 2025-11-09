import math
from typing import Self
from numbers import Real
from collections.abc import Sequence

import numpy as np
import pygame as pg

TILE_OFFSETS = (
    (-1, 1), (0, 1), (1, 1),
    (-1, 0), (0, 0), (1, 0),
    (-1, -1), (0, -1), (1, -1),
)


class Entity(object):
    def __init__(self: Self, level: dict, width: Real=0.5) -> None:
        self.level = level
        self.pos = (0, 0)
        self.velocity2d = (0, 0)
        self.elevation_velocity = 0
        self.yaw_velocity = 0
        self.elevation = 0
        self.yaw = 0
        self.width = width # width of rect
    
    @property
    def pos(self: Self) -> tuple:
        return tuple(self._pos)

    @pos.setter
    def pos(self: Self, value: Sequence) -> None:
        self._pos = pg.Vector2(value)

    @property
    def x(self: Self) -> Real:
        return self._pos.x

    @x.setter
    def x(self: Self, value: Real) -> None:
        self._pos.x = value

    @property
    def y(self: Self) -> Real:
        return self._pos.y

    @y.setter
    def y(self: Self, value: Real) -> None:
        self._pos.y = value

    @property
    def forward(self: Self) -> pg.Vector2:
        return self._yaw

    @property
    def right(self: Self) -> pg.Vector2:
        return self._plane

    @property
    def elevation(self: Self) -> Real:
        return self._elevation

    @elevation.setter
    def elevation(self: Self, value: Real) -> None:
        if value <= -1:
            raise ValueError('elevation must be greater than -1')
        self._elevation = value

    @property
    def yaw(self: Self) -> float:
        return self._yaw_value

    @yaw.setter
    def yaw(self: Self, value: Real) -> None:
        self._yaw_value = value
        self._yaw = pg.Vector2(0, 1).rotate(value)
        self._semiplane = pg.Vector2(-self._yaw.y, self._yaw.x)
        # -1 because direction is flipped
        # the plane is for the camera but it is also the right vector

    @property
    def width(self: Self) -> Real:
        return self._width

    @width.setter
    def width(self: Self, value: Real) -> None:
        self._width = value

    @property
    def velocity2d(self: Self) -> tuple:
        return tuple(self._velocity2d)

    @velocity2d.setter
    def velocity2d(self: Self, value: Sequence) -> None:
        self._velocity2d = pg.Vector2(value)

    @property
    def elevation_velocity(self: Self) -> Real:
        return self._elevation_velocity

    @elevation_velocity.setter
    def elevation_velocity(self: Self, value: Real) -> None:
        self._elevation_velocity = value

    @property
    def yaw_velocity(self: Self) -> Real:
        return self._yaw_velocity

    @yaw_velocity.setter
    def yaw_velocity(self: Self, value: Real) -> None:
        self._yaw_velocity = value

    @property
    def level(self: Self) -> dict:
        return self._level

    @level.setter
    def level(self: Self, value: dict) -> None:
        self._level = value

    def _get_rects_around(self: Self) -> tuple:
        tile = pg.Vector2(math.floor(self._pos.x),
                               math.floor(self._pos.y))
        tiles = []
        for offset in TILE_OFFSETS:
            offset_tile = tile + offset
            level_string = f'{int(offset_tile.x)};{int(offset_tile.y)}'
            if self._level['walls'].get(level_string) != None:
                tiles.append(pg.Rect(offset_tile.x, offset_tile.y, 1, 1))
        return tuple(tiles)

    def rect(self: Self) -> pg.Rect:
        rect = pg.FRect(0, 0, self._width, self._width)
        rect.center = self._pos
        return rect

    def update(self: Self, rel_game_speed: Real) -> None:
        self._elevation += self._elevation_velocity
        if self._yaw_velocity:
            self.yaw += self._yaw_velocity
         
        self._pos.x += self._velocity2d.x * rel_game_speed
        entity_rect = self.rect()
        for rect in self._get_rects_around():
            if entity_rect.colliderect(rect):
                if self._velocity2d.x > 0:
                    entity_rect.right = rect.left
                elif self._velocity2d.x < 0:
                    entity_rect.left = rect.right
                self._pos.x = entity_rect.centerx
        self._pos.y += self._velocity2d.y * rel_game_speed
        entity_rect = self.rect()
        for rect in self._get_rects_around():
            if entity_rect.colliderect(rect):
                if self._velocity2d.y > 0:
                    entity_rect.bottom = rect.top
                elif self._velocity2d.y < 0:
                    entity_rect.top = rect.bottom
                self._pos.y = entity_rect.centery
 

class Player(Entity):
    def __init__(self: Self,
                 level: dict,
                 width: Real=0.5,
                 yaw_sensitivity: Real=0.125,
                 mouse_enabled: bool=1,
                 keyboard_look_enabled: bool=1) -> None:
        super().__init__(level, width)
        self._forward_velocity = pg.Vector2(0, 0)
        self._right_velocity = pg.Vector2(0, 0)
        self._key_statuses = [0, 0, 0, 0, 0, 0]
        # w, s, d, a, right, left
        self._render_elevation = self._elevation
        
        self._settings = {
            'bob_strength': 0,
            'bob_frequency': 0,
        }
        self.yaw_sensitivity = yaw_sensitivity
        self.mouse_enabled = mouse_enabled
        self.keyboard_look_enabled = keyboard_look_enabled

    @property
    def yaw_sensitivity(self: Self) -> Real:
        return self._settings['yaw_sensitivity']

    @yaw_sensitivity.setter
    def yaw_sensitivity(self: Self, value: Real) -> None:
        self._settings['yaw_sensitivity'] = value

    @property
    def mouse_enabled(self: Self) -> bool:
        return bool(self._settings['mouse_enabled'])

    @mouse_enabled.setter
    def mouse_enabled(self: Self, value: bool) -> None:
        self._settings['mouse_enabled'] = value

    @property
    def keyboard_look_enabled(self: Self) -> bool:
        return bool(self._settings['keyboard_look_enabled'])

    @keyboard_look_enabled.setter
    def keyboard_look_enabled(self: Self, value: bool) -> None:
        self._settings['keyboard_look_enabled'] = value

    def handle_events(self: Self, event: pg.Event) -> None:
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_w:
                self._key_statuses[0] = 1
            elif event.key == pg.K_s:
                self._key_statuses[1] = 1
            elif event.key == pg.K_d:
                self._key_statuses[2] = 1
            elif event.key == pg.K_a:
                self._key_statuses[3] = 1
            elif event.key == pg.K_RIGHT:
                self._key_statuses[4] = 1
            elif event.key == pg.K_LEFT:
                self._key_statuses[5] = 1
        elif event.type == pg.KEYUP:
            if event.key == pg.K_w:
                self._key_statuses[0] = 0
            elif event.key == pg.K_s:
                self._key_statuses[1] = 0
            elif event.key == pg.K_d:
                self._key_statuses[2] = 0
            elif event.key == pg.K_a:
                self._key_statuses[3] = 0
            elif event.key == pg.K_RIGHT:
                self._key_statuses[4] = 0
            elif event.key == pg.K_LEFT:
                self._key_statuses[5] = 0
        elif event.type == pg.MOUSEMOTION and self._settings['mouse_enabled']:
            if event.rel[0]:
                self.yaw += event.rel[0] * self._settings['yaw_sensitivity']

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        pg.event.set_grab(1)
        pg.mouse.set_visible(0)

        movement = (self._key_statuses[0] - self._key_statuses[1], # forward
                    self._key_statuses[2] - self._key_statuses[3], # right
                    self._key_statuses[4] - self._key_statuses[5]) # look right

        if movement[0]:
            self._forward_velocity.update(self._yaw * 0.05 * movement[0])
        if movement[1]:
            self._right_velocity.update(self._semiplane * 0.05 * movement[1])
        
        self._yaw_velocity = (
            self._settings['keyboard_look_enabled']
            * self._settings['yaw_sensitivity']
            * movement[2]
            * 18
            * rel_game_speed
        )

        magnitudes = (self._forward_velocity.magnitude(),
                      self._right_velocity.magnitude())
        vel_mult = 0.90625**rel_game_speed
        if magnitudes[0] >= 0.001:
            self._render_elevation = self._elevation + 0.005
            self._forward_velocity *= vel_mult
        else:
            self._forward_velocity.update(0, 0)
        if magnitudes[1] >= 0.001:
            self._render_elevation = self._elevation + 0.005
            # so it will satisfy the below if statement ^
            # where it is actually being calculated
            self._right_velocity *= vel_mult
        else:
            self._right_velocity.update(0, 0)
        if abs(self._render_elevation - self._elevation) >= 0.005:
            # self._render_elevation = render_elevation
            self._render_elevation = self._elevation + (
                math.sin(level_timer * self._settings['bob_frequency'])
                * self._settings['bob_strength']
                * min(self._velocity2d.magnitude() * 20, 2)
            )

        self._velocity2d = self._forward_velocity + self._right_velocity
        super().update(rel_game_speed)
        

class EntityManager(object):
    def __init__(self: Self, *args: Entity) -> None:
        self.entities = list(args)
        # _entities serves as render rules and a list of entities
        # key is the entity
        # value is if the entity should be rendered or not

    @property
    def entities(self: Self) -> tuple:
        return tuple(self._entities)

    @entities.setter
    def entities(self: Self, value: Sequence) -> None:
        self._entities = list(value)

    def add_entity(self: Self, entity: Entity) -> None:
        self._entities.append(entity)

    def remove_entity(self: Self, dex: int) -> None:
        del self._entities[dex]

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        for entity in self._entities:
            entity.update(rel_game_speed, level_timer)



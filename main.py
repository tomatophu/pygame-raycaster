import time
from typing import Self

import pygame as pg

from modules.texture import WallTexture
from modules.texture import FloorTexture
from modules.renderer import Camera
from modules.entities import Player
from modules.entities import EntityManager


class Game(object):

    _SCREEN_SIZE = (960, 720)
    _SURF_RATIO = (3, 3)
    _SURF_SIZE = (
        int(_SCREEN_SIZE[0] / _SURF_RATIO[0]),
        int(_SCREEN_SIZE[1] / _SURF_RATIO[1]),
    )
    _SCREEN_FLAGS = pg.RESIZABLE | pg.SCALED
    _GAME_SPEED = 60

    def __init__(self: Self) -> None:
        pg.init()

        self._settings = {
            'vsync': 1,
        }
        self._screen = pg.display.set_mode(
            self._SCREEN_SIZE,
            flags=self._SCREEN_FLAGS,
            vsync=self._settings['vsync']
        )
        pg.display.set_caption('Pygame Raycaster')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        
        self._level = {
            'walls': {
                '0;0': 0, '1;0': 0, '2;0': 0, '3;0': 0,
                '4;0': 0, '5;0': 0, '6;0': 0, '7;0': 0,
                '8;0': 0, '9;0': 0, '10;0': 0, '0;1': 0,
                '8;1': 0, '10;1': 0, '0;2': 0, '2;2': 0,
                '3;2': 0, '4;2': 0, '5;2': 0, '8;2': 0,
                '9;2': 0, '10;2': 0, '0;3': 0, '2;3': 0,
                '5;3': 0, '10;3': 0, '0;4': 0, '2;4': 0,
                '5;4': 0, '7;4': 0, '8;4': 0, '9;4': 0,
                '10;4': 0, '0;5': 0, '2;5': 0, '3;5': 0,
                '4;5': 0, '5;5': 0, '7;5': 0, '8;5': 0,
                '9;5': 0, '10;5': 0, '0;6': 0, '10;6': 0,
                '0;7': 0, '1;7': 0, '2;7': 0, '4;7': 0,
                '5;7': 0, '6;7': 0, '7;7': 0, '10;7': 0,
                '0;8': 0, '2;8': 0, '4;8': 0, '7;8': 0,
                '10;8': 0, '0;9': 0, '2;9': 0, '4;9': 0,
                '7;9': 0, '10;9': 0, '0;10': 0, '2;10': 0,
                '4;10': 0, '7;10': 0, '10;10': 0, '0;11': 0,
                '1;11': 0, '2;11': 0, '3;11': 0, '4;11': 0,
                '5;11': 0, '6;11': 0, '7;11': 0, '8;11': 0,
                '9;11': 0, '10;11': 0,
            },
        }

        self._wall_textures = [
            WallTexture('data/images/greystone.png'),
        ]
        self._floor_texture = FloorTexture('data/images/redbrick.png')
        
        
        self._player = Player(self._level)
        self._camera = Camera(
            90,
            self._SURF_SIZE[0] / 2,
            6,
            self._wall_textures,
            self._floor_texture,
            self._player,
        )
        self._player.pos = (6.5, 6)
        self._camera.horizon = self._SURF_SIZE[1] / 2
        self._level_timer = 0
    
    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            self._level_timer += delta_time

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                self._player.handle_events(event)

            self._player.update(rel_game_speed, self._level_timer)
            self._camera.render(self._surface)
            pg.display.set_caption(str(1 / delta_time))

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()

if __name__ == '__main__':
    Game().run()


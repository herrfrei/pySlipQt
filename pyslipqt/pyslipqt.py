"""
A "slip map" widget for PyQt5.

Some semantics:
    map   the whole map
    view  is the view of the map through the widget
          (view may be smaller than map, or larger)
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QPainter


# if we don't have log.py, don't crash
try:
#    from . import log
    import log
    log = log.Log('pyslipqt.log')
except AttributeError:
    # means log already set up
    pass
except ImportError as e:
    # if we don't have log.py, don't crash
    # fake all log(), log.debug(), ... calls
    def logit(*args, **kwargs):
        pass
    log = logit
    log.debug = logit
    log.info = logit
    log.warn = logit
    log.error = logit
    log.critical = logit


# version number of the widget
__version__ = '0.1.0'


class PySlipQt(QLabel):

    TileWidth = 256
    TileHeight = 256

    def __init__(self, parent, tile_src, start_level=0, **kwargs):
        """Initialize the pySlipQt widget.

        parent       the GUI parent widget
        tile_src     a Tiles object, source of tiles
        start_level  level to initially display
        kwargs       keyword args passed through to the underlying QLabel
        """

        super().__init__(parent)

        self.tile_src = tile_src

        # the tile coordinates
        self.level = start_level

        # view and map limits
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.view_width = 0     
        self.view_height = 0

        # set tile levels stuff - allowed levels, etc
        self.max_level = max(tile_src.levels)
        self.min_level = min(tile_src.levels)

        self.tile_size_x = tile_src.tile_size_x
        self.tile_size_y = tile_src.tile_size_y

        # define position and tile coords of the "key" tile
        self.key_tile_left = 0      # tile coordinates of key tile
        self.key_tile_top = 0
        self.key_tile_xoffset = 0   # view coordinates of key tile wrt view
        self.key_tile_yoffset = 0

        self.left_mbutton_down = False
        self.mid_mbutton_down = False
        self.right_mbutton_down = False

        self.start_drag_x = None
        self.start_drag_y = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(self.TileWidth, self.TileHeight)

        tile_src.setCallback(self.update)

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.lightGray)
        self.setPalette(p)

#        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        b = event.button()
        if b == Qt.NoButton:
            log('mousePressEvent: button=Qt.NoButton')
        elif b == Qt.LeftButton:
            log('mousePressEvent: button=Qt.LeftButton')
            self.left_mbutton_down = True
        elif b == Qt.MidButton:
            log('mousePressEvent: button=Qt.MidButton')
            self.mid_mbutton_down = True
        elif b == Qt.RightButton:
            log('mousePressEvent: button=Qt.RightButton')
            self.right_mbutton_down = True
        else:
            log('mousePressEvent: unknown button')
         
    def mouseReleaseEvent(self, event):
        b = event.button()
        if b == Qt.NoButton:
            log('mouseReleaseEvent: button=Qt.NoButton')
        elif b == Qt.LeftButton:
            log('mouseReleaseEvent: button=Qt.LeftButton')
            self.left_mbutton_down = False
            self.start_drag_x = None    # end drag, if any
            self.start_drag_y = None
        elif b == Qt.MidButton:
            log('mouseReleaseEvent: button=Qt.MidButton')
            self.mid_mbutton_down = False
        elif b == Qt.RightButton:
            log('mouseReleaseEvent: button=Qt.RightButton')
            self.right_mbutton_down = False
        else:
            log('mouseReleaseEvent: unknown button')
 
    def mouseDoubleClickEvent(self, event):
        b = event.button()
        if b == Qt.NoButton:
            log('mouseDoubleClickEvent: button=Qt.NoButton')
        elif b == Qt.LeftButton:
            log('mouseDoubleClickEvent: button=Qt.LeftButton')
        elif b == Qt.MidButton:
            log('mouseDoubleClickEvent: button=Qt.MidButton')
        elif b == Qt.RightButton:
            log('mouseDoubleClickEvent: button=Qt.RightButton')
        else:
            log('mouseDoubleClickEvent: unknown button')
 
    def mouseMoveEvent(self, event):
        """Handle a mouse move event."""

        x = event.x()
        y = event.y()

        if self.left_mbutton_down:
            if self.start_drag_x:       # if we are already dragging
                delta_x = self.start_drag_x - x
                delta_y = self.start_drag_y - y
                self.normalize_view(delta_x, delta_y)   # normalize the "key" tile
                self.update()                           # force a repaint

            self.start_drag_x = x
            self.start_drag_y = y

    def normalize_view(self, delta_x=None, delta_y=None):
        """After drag/zoom, set "key" tile correctly.

        delta_x  the X amount dragged (pixels), None if not dragged
        delta_y  the Y amount dragged (pixels), None if not dragged
        """

        if delta_x:
            if self.tile_src.wrap_x:
                # wrapping in X direction, move 'key' tile
                self.key_tile_xoffset -= delta_x
                # normalize the 'key' tile coordinates
                while self.key_tile_xoffset > 0:
                    self.key_tile_xoffset -= self.tile_size_x
                    self.key_tile_left += 1
                    self.key_tile_left %= self.num_tiles_x
                while self.key_tile_xoffset <= -self.tile_size_x:
                    self.key_tile_xoffset += self.tile_size_x
                    self.key_tile_left -= 1
                    self.key_tile_left = ((self.key_tile_left + self.num_tiles_x)
                                             % self.num_tiles_x)
            else:
                # if view > map, don't drag, ensure centred
                #if 
                # map > view, allow drag
    #                    self.view_offset_x += self.start_drag_x - x
                pass

        if delta_y:
            if self.tile_src.wrap_y:
                # wrapping in Y direction, move 'key' tile
                self.key_tile_yoffset -= delta_y
                # normalize the 'key' tile coordinates
                while self.key_tile_yoffset > 0:
                    self.key_tile_yoffset -= self.tile_size_y
                    self.key_tile_top += 1
                    self.key_tile_top %= self.num_tiles_y
                while self.key_tile_yoffset <= -self.tile_size_y:
                    self.key_tile_yoffset += self.tile_size_y
                    self.key_tile_top -= 1
                    self.key_tile_top = ((self.key_tile_top + self.num_tiles_y)
                                            % self.num_tiles_y)
            else:
                # if view > map, don't drag
                # map > view, allow drag
    #                    self.view_offset_y += self.start_drag_y - y
                pass

    def keyPressEvent(self, event):
        """Capture a keyboard event."""

        log(f'key press event={event.key()}')

    def keyReleaseEvent(self, event):

        log(f'key release event={event.key()}')

    def wheelEvent(self, event):
        """Handle a mouse wheel rotation."""

        log(f"wheelEvent: {'UP' if event.angleDelta().y() < 0 else 'DOWN'}")

        if event.angleDelta().y() < 0:
            new_level = self.level + 1
        else:
            new_level = self.level - 1
        self.use_level(new_level)

    def use_level(self, level):
        """Use new map level.

        level  the new level to use

        This code will try to maintain the centre of the view at the same
        GEO coordinates, if possible.  The "key" tile is updated.

        Returns True if level change is OK, else False.
        """

        return self.zoom_level(level)

    def resizeEvent(self, event):
        """Widget resized, recompute some state."""

        # new widget size
        self.view_width = self.width()
        self.view_height = self.height()

        # recalculate the "top left" tile stuff
        self.recalc_wrap()

    def recalc_wrap(self):
        """Recalculate the "top left" tile information."""

        pass

    def paintEvent(self, event):
        """Draw the base map and then the layers on top."""

        log(f'paintEvent: self.key_tile_left={self.key_tile_left}, self.key_tile_xoffset={self.key_tile_xoffset}')

        ######
        # The "key" tile position is maintained by other code, we just
        # assume it's set.  Figure out how to draw tiles, set up 'row_list' and
        # 'col_list' which are list of tile coords to draw (row and colums).
        ######

        col_list = []
        x_coord = self.key_tile_left
        x_pix_start = self.key_tile_xoffset
        while x_pix_start < self.view_width:
            col_list.append(x_coord)
            if not self.tile_src.wrap_x and x_coord >= self.num_tiles_x-1:
                break
            x_coord = (x_coord + 1) % self.num_tiles_x
            x_pix_start += self.tile_src.tile_size_x

        row_list = []
        y_coord = self.key_tile_top
        y_pix_start = self.key_tile_yoffset
        while y_pix_start < self.view_height:
            row_list.append(y_coord)
            if not self.tile_src.wrap_y and y_coord >= self.num_tiles_y-1:
                break
            y_coord = (y_coord + 1) % self.num_tiles_y
            y_pix_start += self.tile_src.tile_size_y

        ######
        # Ready to update the view
        ######

        # prepare the canvas
        painter = QPainter()
        painter.begin(self)

        # paste all background tiles onto the view
        x_pix = self.key_tile_xoffset
        for x in col_list:
            y_pix = self.key_tile_yoffset
            for y in row_list:
                QPainter.drawPixmap(painter, x_pix, y_pix,
                                    self.tile_src.GetTile(x, y))
                y_pix += self.tile_size_y
            x_pix += self.tile_size_x

        painter.end()

################################################################################
# Below are the "external" API methods.
################################################################################

    def zoom_level(self, level):
        """Zoom to a map level.

        level  map level to zoom to

        Change the map zoom level to that given. Returns True if the zoom
        succeeded, else False. If False is returned the method call has no effect.
        """

        result = self.tile_src.UseLevel(level)
        if result:
            self.level = level
            (self.num_tiles_x, self.num_tiles_y, _, _) = self.tile_src.GetInfo(level)
            self.update()
        return result

    def pan_position(self, posn):
        """Pan to the given position in the current map zoom level.

        posn  a tuple (xgeo, ygeo)
        """

        pass

    def zoom_level_position(self, level, posn):
        """Zoom to a map level and pan to the given position in the map.

        level  map level to zoom to
        posn  a tuple (xgeo, ygeo)
        """

        pass

    def zoom_area(self, posn, size):
        """Zoom to a map level and area.

        posn  a tuple (xgeo, ygeo) of the centre of the area to show
        size  a tuple (width, height) of area in geo coordinate units

        Zooms to a map level and pans to a position such that the specified area
        is completely within the view. Provides a simple way to ensure an
        extended feature is wholly within the centre of the view.
        """

        pass

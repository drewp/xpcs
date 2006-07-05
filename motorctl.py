from __future__ import division
import atexit, sys, time
from louie import dispatcher
from twisted.internet import reactor
sys.path.append("/home/drewp/projects/light9/light9/io")
try:
    import parport
    parport.getparport()
except ImportError:
    class _:
        def outdata(self, *args):
            pass
    parport = _()

class Ctl:
    def __init__(self):
        self.blade = False
        self.xpos = 0
        self.ypos = 0

        self.offTimer = None

        dispatcher.connect(self.dragTo, "dragto")
        self.path = [] # future points to walk to
        self.lastByteTime = 0
        atexit.register(lambda: self.out(0))

    def resetPos(self):
        self.xpos = self.ypos = 0
        dispatcher.send("coords", x=self.xpos, y=self.ypos)
        self.update()

    def off(self):
        self.out(0)
        
    def dragTo(self, x, y, now=False, blade=False):
        self.path.append((x, y, blade))
        #print "drag to", x, y, len(self.path)
        dispatcher.send("new path", path=self.path)
        if now:
            while self._step():
                print "stepping now"
                pass

    def step(self, runFor=.05):
        start = time.time()
        more = True
        while time.time() - start < .05 and more:
            more = self._step()

    def _step(self):
        if not self.path:
            if self.offTimer is None or self.offTimer.called:
                self.offTimer = reactor.callLater(.1, self.off)
            return False

        if self.offTimer is not None and not self.offTimer.called:
            self.offTimer.reset(.1)

        goal = self.path[0]
        
        goal = int(goal[0]), int(goal[1]), goal[2]
        print "at %s, to %s, %s lines left" % (
            (self.xpos, self.ypos), goal, len(self.path))
        self.setBlade(goal[2])
        if (self.xpos, self.ypos) == goal[:2]:
            self.path.pop(0)
            dispatcher.send("new path", path=self.path)
            return True
        self.move(cmp(goal[0], self.xpos),
                  cmp(goal[1], self.ypos))
        return True

    def move(self, dx, dy):
        if dx == dy == 0:
            return
        if abs(dx) > 1 or abs(dy) > 1:
            print "========================= dx=%s dy=%s ======================" % (dx,dy)
        self.xpos += dx
        self.ypos += dy
        dispatcher.send("coords", x=self.xpos, y=self.ypos)
        #print "x=%d y=%d" % (self.xpos, self.ypos)
        self.update()

    def update(self):
        byte = 0
        if self.blade:
            byte |= 0x80

        byte |= (0x01, 0x03, 0x02, 0x00)[self.xpos % 4] * 0x20
        byte |= (0x01, 0x03, 0x02, 0x00)[self.ypos % 4] * 0x04

        byte |= 0x01 # power pin
        byte |= 0x02 | 0x10 # enable dirs

        now = time.time()
#        print "%.1fms delay between bytes" % ((now - self.lastByteTime) * 1000)
        self.out(byte)
        self.lastByteTime = now
        
    def out(self, byte):
        #print hex(byte)
        parport.outdata(byte)
        # at .0014, Y loses steps
        # at .002, Y still loses
        time.sleep(.003)

    def toggleBlade(self):
        self.setBlade(not self.blade)
        
    def setBlade(self, which):
        if which == self.blade:
            return
        self.blade = which
        if self.blade:
            # blade needs full power to go down
            self.out(0x80)
            time.sleep(.05)
        self.update()

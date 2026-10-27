import sys; sys.path.insert(0, '/state'); import kit, time
g, update = kit.load('/state/dev_jump', 'mona_jump')
g['state']['tilt'] = False
cost, raw = kit.step(update); kit.shot('title', raw, cost)
kit.step(update, (BUTTON_SELECT,))
worst, avg, raw = kit.run_for(update, 1200); kit.shot('first bounces', raw, avg); print('  avg', avg, 'worst', worst, 'score', g['score'])
# steer toward whichever platform is above and keep climbing for a while
def chase(ms):
    start = time.ticks_ms(); worst = 0
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        p = g['player']
        above = [pl for pl in g['platforms'] if pl[1] < p[1] and pl[5] is None]
        target = min(above, key=lambda pl: p[1] - pl[1])[0] + 8 if above else p[0]
        buttons = (BUTTON_RIGHT,) if target > p[0] + 6 else ((BUTTON_LEFT,) if target < p[0] - 6 else ())
        cost, raw = kit.step(update, buttons); worst = max(worst, cost)
        if g['mode'] != g['PLAY']: break
    return worst, raw
worst, raw = chase(6000); kit.shot('climbing', raw, worst); print('  after chase: score', g['score'], 'mode', g['mode'], 'platforms', len(g['platforms']), 'kinds', [pl[2] for pl in g['platforms']][:12], 'springs', sum(1 for pl in g['platforms'] if pl[4]))
worst, raw = chase(8000); kit.shot('higher', raw, worst); print('  score', g['score'], 'mode', g['mode'], 'worst frame', worst)
if g['mode'] == g['PLAY']:
    g['player'][1] = g['camera_y'] + 400   # fall off the bottom
    ok, raw, cost = kit.run_until(update, lambda: g['mode'] == g['OVER'], 2000)
_, avg, raw = kit.run_for(update, 700); kit.shot('game over', raw, avg)
g['on_exit'](); print('DONE jump state', g['state'])

# Minesweeper

Minesweeper in the browser. Play here: https://kevinalbs.com/minesweeper/

![Minesweeper Gameplay](./img/minesweeper-gameplay.gif)


# Reporting a bug

When reporting a bug, please include the JSON form of the grid used. This may help to reproduce the issue.
Run the following in Developer Tools:
```js
// Copy the grid JSON to the clipboard
copy (game.get_grid_json())
```
And paste the result in the bug report.
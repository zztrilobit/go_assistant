# go_assistant
Go game GUI on Python


Тренажер для игры Го - визуальный интерфейс к GTP - совместимым программам, таким как 
GNUGO, FUEGO и т.д.  Цель интерфейса - начинающий игрок часть ходов делает самостоятельно,
а часть - с подсказкой, уменьшая долю последних по мере накопления опыта игры.

Обучение любой деятельности состоит из следующих этапов

 - наблюдение за деятельностью другого

 - постепенное включение в процесс, частично замещаем опытного участника

 - действуем сами, иногда спрашивая совета

 - действуем полностью самостоятельно

Обучающая среда позволяет имитировать прохождение этих этапов начинающим игроком 



Версии:

0.0.7 - сохранение настрочных параметров, багофиксы (2017.21.03)

0.0.6 - подключил код расчета позиции. Начало тестирования с leela  (2017.20.03)

0.0.5 - код для расчета позиции на доске после цепочки ходов. нужен, т.к. некоторые движки 
(как минимум leela) не поддерживают команду "получить список камней"

0.0.4 - упрощение структуры, сериализация линии игры в pickle

0.0.3 - исправление ошибок сохранения

0.0.2 - сохранение sgf

0.0.1 - задан ритм для подсказки. Допустим при вводе ритма yn ход с подсказкой будет 
чередоваться с самостоятельным, yyn - два с подсказкой один самостоятельно.

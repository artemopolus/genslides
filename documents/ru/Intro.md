## Введение

В этой статье я хочу поделится своей программой (лицензия MIT), которая была разработана мной на базе опыта работы с LLM (преимущественно GPT и некоторые из локальных моделей). OpenAI, Anthropic и другие компании сфокусировались в своих разработках на системы стиля **Одна кнопка**. Я же провел такой сам-себе-НИОКР в направлении более сложной работы с использованием техник **Деревьев Размышлений** (Trees-of-Thoughts), ориентируясь на нестандартные техники работы с LLM.

### Краткое описание программы

Область LLM (Large Language Model) — это одна из ярчайших и известных достижений ИТ-индустрии последних лет, представляющий собой тип нейронных моделей, обученный на больших объемах текстовых данных, что позволяет генерировать человекоподобный текст. В настоящее время наиболее распространенный формат работы с LLM заключается в том, что пользователь задает вопрос и получает ответ. Этот метод общения очень прост и интуитивно понятен, а осуществляется через текстовые сообщения, аналогично обычному чату, что делает его понятным для большинства пользователей.

В более продвинутом случае взаимодействия с LLM можно составить диалог, последовательно задавая вопросы. Такой подход позволяет глубже исследовать обсуждаемые темы, следуя методу "от простого к сложному", получать развернутые ответы и задавать наводящие вопросы, что делает общение более естественным и интерактивным в виде совместного изучения вопроса с ассистентом. Однако при этом возникает проблема: пользователи часто сталкиваются с повторением одного и того же сценария, когда им приходится полностью удалять предыдущий диалог и начинать новый. Это происходит из-за недостатков текущих инструментов, ограничивающих загрузку, сохранение или изменение контекста, информации из предыдущих сообщений, что приводит к неудобствам для пользователей.

Иногда пользователи пытаются предотвратить это, подготавливая краткие выводы на базе важных аспектов диалога перед тем, как начать новый разговор. Техническая причина этого заключается в ограниченном контекстном окне, которое сужает объем информации, использующейся моделью для формирования ответа, но в некоторых случаях сам ход обсуждения может завести в тупик. Поэтому приходится создавать новый диалог, а вся тяжесть по сохранению и загрузке контекста ложится на пользователя.

Одним из ключевых аспектов является использование примеров в промпте, что способствует лучшему пониманию задач ассистентом. Это предположение подводит нас к важному аспекту взаимодействия: генерация примеров и работа с иерархией сообщений могут значительно улучшить диалог. Рассмотрим подробнее, как внедрение этих методов, а также исследование различных ролей сообщений положительно влияет на качество общения с моделями LLM, а также как новые технологии и подходы могут привести к оптимизации процессов и улучшению результатов в различных областях применения.

 - [Исследования](./documents/parts/research.md)

Представляемая программа предназначена для работы с LLM и предлагает новые методы взаимодействия. Основная концепция использования программы базируется на том же принципе диалога и заключается в чередовании вопросов и ответов. Инструменты позволяют пользователю изменять любое сообщение диалога, а после обновлять его. Хоть целиком, если изменения были произведены с первым сообщением. Однако он может и продолжать его с середины уже существующего, получая два диалога из одного. Этот инструмент предназначен, чтобы сделать общение более гибким и персонализированным:
- Можно попытаться найти место, где диалог свернул к тупиковым выводам.
- Можно рассмотреть иной аспект проблемы.
- Можно обогатить запрос новыми деталями.

Главное -- старые сообщения останутся в распоряжении пользователя. Создаваемые диалоги отображаются в виде ветвей, что позволяет визуально структурировать общение, которое теперь состоит из серии взаимосвязанных диалогов.

Если ветви имеют некоторое количество общих сообщений, они формируют дерево диалогов. Эта конструкция помогает пользователю легко отслеживать взаимосвязи между различными направлениями обсуждения. В результате появляется так называемое "дерево размышлений", которое облегчает исследование различных вариантов ответов и подходов к вопросам, структурируя мышление и позволяя пользователю лучше анализировать полученную информацию.

Следующий этап работы с LLM предоставляет пользователю возможность не только задавать вопросы, но и более гибко управлять процессом диалога. Важно подчеркнуть, что благодаря систематизации информации и созданию структуры из нескольких ветвей, пользователю становится легче ориентироваться в обсуждении, применяя инструменты для обновления и изменения диалогов. Таким образом, переходим к интуитивным инструкциям, которые помогут пользователям быстро освоиться в использовании программы и эффективно взаимодействовать с различными функциональностями.


### Инструкция по началу работы с программой

1. **Установите имя сессии в поле `Session name`**. Сессия -- основное пространство работы пользователя, где сохраняются все диалоги и задачи. Правильное имя сессии поможет позже легко идентифицировать её среди других сохранённых сессий.

2. **Создайте сессию кнопкой `New name for session`**. Эта кнопка является элементом интерфейса, позволяющим пользователю инициировать создание новой сессии. Создание новой сессии позволит начать новый цикл работы, не теряя данные из предыдущих сессий.

3. **Выберите папку для текущей работы кнопкой `Load actioner from location` и выберите папку назначения**. Папка — это место на компьютере, где пользователь может сохранить свои файлы и данные отдельного проекта. Правильный выбор папки позволяет удобно организовать файлы и быстро находить их в будущем.

### Инструкция по созданию простейшей пары вопрос-ответ

4. **Введите текст запроса во вкладке Prompt поле Prompt**. Вкладка — это часть интерфейса, где осуществляется ввод данных, а поле — это конкретное место для ввода текста. Текст запроса должен быть сформулирован четко, чтобы LLM мог дать на него адекватный ответ.

5. **Создайте подзадачу через вкладку Prompt кнопку Request**. Подзадача — это отдельный шаг в процессе диалога, который следует за основным запросом. Создание подзадачи позволяет детализировать запрос и уточнить, какой именно информации пользователь ожидает.

6. **Перейдите на вкладку обновления Step Navigation**. Процесс обновления позволяет пользователю обновить все предыдущие сообщения и ветви диалога. Обновление помогает увидеть актуальные ответы на ранее заданные вопросы.

7. **Обновите все ветки через кнопку Update All Trees (UAT)**. Ветки — это части дерева диалога, которые содержат различающиеся линии обсуждения. Обновление всех веток позволяет синхронизировать информацию между различными ветвями, улучшая взаимодействие с LLM.

Эти итерации можно многократно повторять для создания диалога. Это основной цикл работы с программой.

### Инструкция по ветвлению или созданию пары диалогов

8. **Используя кнопки перемещения, перейдите на целевое сообщение Go up, Go down**. Кнопки перемещения позволяют пользователю перемещаться по структуре диалога, поднимаясь или опускаясь по ветвям. Навигация между сообщениями помогает выбрать нужное сообщение для дальнейшей работы.

9. **Введите сообщение во вкладке Prompt поле Prompt**. Сообщение — это текст, который пользователь хочет использовать как новый запрос в диалоге. Четкость формулировок сообщения обеспечивает более точные ответы от LLM.

10. **Создайте подзадачу во вкладке Prompt поле Request**. Это действие подразумевает создание более детализированного вопроса или запроса. Добавление подзадачи улучшает структуру диалога и помогает пользователю получить более конкретные ответы на уточняющие вопросы.

Теперь в дереве два диалога, между которыми можно переключаться, используя кнопки навигации. Дерево диалогов обеспечивает отображение различных ветвей и их взаимосвязей, а возможность переключения между диалогами позволяет пользователю легко возвращаться к различным аспектам обсуждения и следить за ходом размышления.

Перед тем как углубиться в возможности редактирования веток и создания диалогов с автоматическим ветвлением, важно понять, как правильно структурировать основные этапы работы с программой. Обсуждая процесс создания простейших пар вопросов и ответов, мы установили базовые принципы взаимодействия с инструментом, которые готовят нас к более сложным действиям, таким как редактирование и ветвление диалогов. Теперь давайте рассмотрим, как можно использовать функции изменения промпта для роста и адаптации диалогов к различным сценариям.


### Документы

 - [Основные моменты](./documents/ru/modules/basics.md)
 - [Примеры](./documents/ru/modules/examples.md)
 - [Ветвление](./documents/ru/modules/branches.md)



## Преимущества и недостатки

Проект **направлен на продвинутых пользователей**, таких как **промпт инженеры**, которые желают испробовать новые методы работы с языковыми моделями, основанными на технологии LLM (Large Language Model). Эти пользователи имеют опыт работы с языковыми моделями и стремятся улучшить эффективность своих взаимодействий с ними.

### Достоинства проекта:
1. **Работа с любыми LLM моделями, используя OpenAI API**: Эта функция предоставляет пользователям гибкость, позволяя подключать различные языковые модели, разработанные компанией OpenAI, и использовать их в своих проектах. Это открывает возможность экспериментировать с разнообразными функциями моделей.

2. **Гибкость манипуляции диалогами и повторное использование их частей**: Пользователи могут редактировать, копировать и вставлять сообщения, а также сохранять фрагменты диалогов для дальнейшего использования. Это делает работу более эффективной и экономит время.

3. **Автоматизация процессов построения диалогов**: Программа предлагает инструменты для создания шаблонов и использования заранее определённых структур, что позволяет пользователям быстро реагировать на запросы и снизить нагрузку.

4. **Сохранение прогресса работы и возможность его загрузки**: Пользователи могут хранить свои диалоги и настройки, что особенно полезно при работе над долгосрочными проектами и обеспечивает возможность вернуться к прежним этапам работы.

5. **Скрытие неиспользуемых элементов диалога**: Эта функция позволяет минимизировать визуальный беспорядок, помогая пользователям сосредоточиться на актуальных частях диалога и облегчать работу.

6. **Новый взгляд на процесс работы с LLM**: Проект предлагает инновационные методы и инструменты, которые изменяют традиционные подходы к взаимодействию с языковыми моделями, делая процесс более интерактивным и адаптивным.

### Недостатки проекта:
1. **Перегруженность интерфейса**: Сложный интерфейс может затруднять взаимодействие и создавать путаницу у пользователей, особенно у новичков, что может негативно сказаться на общем опыте использования.

2. **Неудобство навигации по деревьям**: Навигация в структуре диалогов может быть сложной, особенно при наличии большого количества задач и веток, что приводит к снижению удобства при использовании.

3. **Перегруженность кода экспериментальными функциями**: Избыточность функций может приводить к ошибкам и сбоям, а также запутыванию пользователей, что требует регулярной отладки и улучшений.

4. **Отсутствие документации**: Недостаток инструкций и обучающих материалов затрудняет освоение программы для новых пользователей, что может ограничить её популярность и распространение.

5. **Неинтуитивные названия элементов интерфейса**: Неясные и сложные названия могут вызывать путаницу и затруднять использование программы для новых пользователей, что подчеркивает необходимость в ясности и доступности интерфейса.

Таким образом, проект предоставляет целый ряд **достоинств**, которые делают его полезным инструментом для работы с LLM, но одновременно необходимо учитывать и текущие **недостатки**, которые могут повлиять на пользовательский опыт.

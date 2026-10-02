# 输入样例：口语字幕片段

> 这是**演示用的构造样例**，用来说明「输入长什么样」。
> 真实字幕通常数千行，这里只截取一小段。

---

```
[00:00:00] so, um, thanks for having me, it's, it's really great to be here
[00:00:04] today I wanna talk about something that, you know, sounds
[00:00:08] kind of counterintuitive at first, which is: goals are for losers.
[00:00:14] and, um, I mean that literally, by the way. this is not, like,
[00:00:18] a metaphor or anything.
[00:00:21] so here's what I mean. when I was at Berkeley getting my MBA,
[00:00:26] everyone around me was, like, super into SMART goals, right?
[00:00:31] you know, specific, measurable, achievable, all that stuff.
[00:00:35] and I remember sitting there thinking, this doesn't feel right.
[00:00:39] because here's the thing — if you have a goal, you're,
[00:00:43] you're basically putting yourself in a state of, of continuous
[00:00:47] failure until you hit it. right? like, every single day
[00:00:51] you wake up and you haven't achieved your goal yet, so you fail again.
[00:00:56] that's, that's a terrible way to live.
[00:01:00] what I started doing instead was building systems.
[00:01:04] a system is something you do on a regular basis,
[00:01:07] something where the process itself is the reward.
[00:01:11] so, like, my writing practice. I don't have a goal of
[00:01:15] writing a book. I have a system of writing every morning
[00:01:18] for two hours. and, you know, the book sort of happens
[00:01:22] as a side effect.
[00:01:24] now, someone asked me last week — actually it was at a conference —
[00:01:28] they said, doesn't that mean you never achieve anything big?
[00:01:32] and I said, no, it's the opposite. I've achieved way more
[00:01:36] than most of my MBA classmates, precisely because I wasn't
[00:01:40] sitting around waiting to feel successful.
```

---

## 这份输入里有什么

| 特征 | 位置 |
|---|---|
| 口语填充词 | `um`、`you know`、`like`、`so`、`actually` |
| 结巴与自我重复 | `it's, it's`、`you're, you're basically`、`that's, that's` |
| 开场寒暄 | `thanks for having me` |
| **实质内容** | 核心主张、伯克利 MBA 的背景、SMART 目标作为对照、目标的心理学论证、系统的定义、写作实践的例子 |
| 对谈交锋 | 上周会议上有人质疑「那岂不是一事无成」+ 讲者的反驳 |

⚠️ **只有前三类的具体 filler 能删，后面两项是实质内容，必须保留。**

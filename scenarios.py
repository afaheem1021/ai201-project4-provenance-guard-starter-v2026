"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

import calibration

# ⚠️ HONEST NOTE ON CRITERION 1. Criterion 1 asks for 10 pieces I wrote myself.
# I did not supply my own writing for this run. The ten pieces below are
# STAND-INS: written by an AI assistant (Claude) in a casual, everyday,
# first-person style to imitate how a student writes. They are not my writing,
# so criterion 1's result below is about these stand-ins, not about me. To do
# this properly, replace HUMAN_STAND_INS with ten real pieces and re-run.
# Frozen on 2026-11-08 before the first eval run.
HUMAN_STAND_INS = [
    # 1 commute (plain)
    "The 7:40 bus was late again today. I stood at the stop for twenty minutes with my coffee getting cold. When it finally came it was packed, so I stood the whole way holding the pole next to a guy eating chips. I got to class right as the professor was taking attendance. She looked at me but didn't say anything. I think I'm going to start leaving at 7:15 even though I hate waking up that early. Or maybe I'll just bike when it gets warmer.",
    # 2 cooking (plain)
    "I tried making my mom's lentil soup last night and it did not taste like hers. I used the same stuff, I think. Onions, garlic, cumin, red lentils, a lemon at the end. Mine came out kind of flat. I called her and she laughed and said I forgot to fry the spices first and also I probably didn't put enough salt. She was right about the salt. I'm going to try again on Sunday and actually write down what she says this time.",
    # 3 exam (plain)
    "Studied for the stats midterm at the library until it closed. I still don't really get confidence intervals. I can do the formula but if you ask me what it means I kind of freeze. My friend tried to explain it with a fishing net and that helped a little. The test is Thursday. I made flashcards but half of them are just me writing 'ask about this' on the back, which isn't great.",
    # 4 part-time job (plain)
    "Worked a double at the store on Saturday because Marcus called out. The morning was dead, maybe ten customers before noon. Then around three a whole youth soccer team came in for snacks and it was chaos. One kid tried to pay with a gift card from a different store. I was on my feet for eleven hours and my back still hurts. The manager bought everyone pizza at the end though, so that was nice.",
    # 5 soccer
    "We lost 3-2 on Sunday and honestly we deserved it. Our first half was a mess. Nobody was talking, and twice I passed straight to the other team, which, great. Second half we woke up. Danny scored off a corner and I almost got one in the last minute but it hit the post. The sound of the ball hitting the post is the worst sound in the world. We play them again in three weeks.",
    # 6 phone (plain)
    "My phone fell out of my pocket on the stairs and the screen cracked into a spiderweb. It still works but I can't see the top left corner, which is where my email is, of course. The repair shop wanted ninety dollars. I'm not paying that right now. So I put a screen protector over the cracks and now it looks like the phone is wearing a bandage. My little sister thinks it's hilarious.",
    # 7 grandparents
    "Every summer we drove eight hours to my grandparents' house, and every summer my dad swore he'd leave earlier next year. He never did. I remember the back seat more than the trip itself: the cooler of sandwiches, my brother's elbow, the tape that only had one side that worked. My grandma would be on the porch before the car even stopped. She's been gone four years now. I still can't smell cardamom without thinking about that porch.",
    # 8 moving
    "Moving apartments is the worst. I thought I had maybe fifteen boxes of stuff. It was thirty-one. Where did all of it come from? I found three phone chargers that don't fit any phone I own and a birthday card from 2019 that I never opened. My friend helped me carry the couch up four flights and we had to take the legs off to get it around the corner. I owe him dinner. Probably several dinners.",
    # 9 coding
    "I spent two hours last night on a bug that turned out to be a missing comma. Two hours. I read the error message like ten times and it kept pointing at the wrong line, or at least I thought it was the wrong line. When I finally saw it I wasn't even happy, I was just tired. My roommate said that's how it goes and that it gets better. I hope he's right because I have another assignment due Friday.",
    # 10 side project
    "I've been building a little app to track my runs because the one I was using got a subscription. Right now it can show a list of runs and that's about it. The login part keeps breaking. I wanted to finish it before the spring 5K but that's in two weeks and I don't think that's happening. Still, the first time I saw my own list show up on my phone I kind of yelled.",
]

# Criterion 2's comparison group: AI-generated (by Claude) on the same ten
# topics, roughly the same length, in the default polished assistant style.
AI_MATCHED = [
    "Public transportation plays an important role in the daily lives of many students. Relying on the bus can be challenging, especially when delays occur unexpectedly. Arriving late to class can create stress and disrupt the learning process. To address this issue, students can plan ahead by leaving earlier and checking real-time schedules. Additionally, alternative options such as cycling can provide greater flexibility and health benefits. Ultimately, effective planning can help make the daily commute a more manageable and positive experience.",
    "Cooking traditional family recipes is a meaningful way to stay connected to one's cultural heritage. However, recreating a dish exactly can be surprisingly difficult. Small details, such as the order in which spices are added or the amount of salt used, can significantly affect the final flavor. Asking family members for guidance and writing down their instructions can help preserve these recipes. With patience and practice, anyone can learn to prepare the dishes they grew up enjoying.",
    "Preparing for a statistics exam requires both understanding and practice. Many students find concepts such as confidence intervals challenging because they involve interpreting results rather than simply applying formulas. Using analogies and real-world examples can make these ideas easier to grasp. In addition, creating flashcards and studying with peers can reinforce key concepts. By starting early and reviewing consistently, students can approach their exams with greater confidence and achieve better results.",
    "Working in retail can be both demanding and rewarding. Long shifts often require employees to stay focused and adaptable, especially when customer traffic changes throughout the day. Busy periods can be stressful, but they also provide opportunities to develop valuable skills such as communication and problem-solving. Supportive managers play an important role in maintaining team morale. Simple gestures of appreciation can make a significant difference in how employees feel about their work.",
    "Losing a close soccer match can be a valuable learning experience for any team. A slow start often highlights the importance of communication and coordination on the field. Teams that make adjustments at halftime can significantly improve their performance in the second half. Moments such as narrowly missed shots can be frustrating, but they also motivate players to keep improving. With focused practice, the team can prepare effectively for the next match.",
    "A cracked phone screen is a common and frustrating problem. Even when the device continues to function, damage to the display can make everyday tasks more difficult. Professional repairs can be expensive, which leads many people to look for temporary solutions such as screen protectors. While these options may help in the short term, it is important to consider the long-term costs and benefits. Using a protective case can help prevent similar damage in the future.",
    "Family road trips often create some of the most lasting childhood memories. The long hours spent traveling, the snacks packed for the journey, and the excitement of arriving at a loved one's home all contribute to a sense of tradition. Grandparents frequently play a central role in these experiences, offering warmth and a sense of belonging. Even years later, familiar sights and smells can bring these memories back, reminding us of the importance of family connections.",
    "Moving to a new apartment can be a challenging and time-consuming process. Many people underestimate how many belongings they have until they begin packing. Sorting through items provides an opportunity to declutter and decide what is truly necessary. Large furniture can present additional difficulties, especially in buildings with narrow staircases. Having friends or family members help with the move can make the process more efficient and enjoyable.",
    "Debugging is an essential skill for anyone learning to program. Small errors, such as a missing comma, can cause frustrating problems that are difficult to identify. Error messages are helpful, but they do not always point directly to the source of the issue. Developing patience and a systematic approach to troubleshooting can make debugging more manageable. Over time, programmers become more efficient at recognizing common mistakes and resolving them quickly.",
    "Building a personal app is an excellent way to develop practical programming skills. Starting with a simple feature, such as displaying a list of items, allows developers to make steady progress. More complex features, such as user authentication, often present additional challenges. Setting realistic goals and deadlines can help maintain motivation throughout the project. Seeing an idea come to life on a real device can be a highly rewarding experience.",
]

SCENARIOS = [
    {
        "name": "own writing stand-ins",
        "criterion": 1,
        "texts": HUMAN_STAND_INS,
    },
    {
        # Criterion 2 compares this group's mean score with the group above.
        "name": "matched AI set",
        "criterion": 2,
        "texts": AI_MATCHED,
    },
    {
        # The six frozen development fixtures from unit 7, in calibration.py order.
        "name": "label coverage fixtures",
        "criterion": 3,
        "texts": [f["text"] for f in calibration.FIXTURES],
    },
    # Criterion 4 (appeals) can't be tested by sending text alone. It lives in
    # tools/eval_appeals_and_raw.py, which runs it three times the same way.
    {
        # Criterion 5: every bad body that can be written as a dict. Malformed
        # JSON, a bare list, and invalid appeals can't be sent by run_eval.py,
        # so tools/eval_appeals_and_raw.py covers those (and re-checks these).
        "name": "bad input",
        "criterion": 5,
        "bodies": [
            {"creator_id": "eval_bad_missing_text"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": 12345, "creator_id": "eval_bad_number"},
            {"text": "   \n\t ", "creator_id": "eval_bad_whitespace"},
            {"text": "Some real words here for the check."},
            {"text": "Some real words here for the check.", "creator_id": ""},
            {"text": "Some real words here for the check.", "creator_id": "x" * 101},
            {"text": "x" * 10_001, "creator_id": "eval_bad_long_text"},
            {"text": "x" * 100_001, "creator_id": "eval_bad_huge_body"},
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems

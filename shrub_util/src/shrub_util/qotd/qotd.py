import secrets


class QuoteOfTheDay:
    def __init__(self):
        self.quotes = [
            {
                "quote": "A nod’s as good as a wink to a blind bat, eh?",
                "source": "Monty Python",
            },
            {
                "quote": "And now for something completely different.",
                "source": "Monty Python",
            },
            {
                "quote": "Is your wife a…’goer’… eh? Know what I mean? "
                "Know what I mean? Nudge nudge. "
                "Nudge nudge! Know "
                "what I mean? Say no more…Know what I mean?",
                "source": "Monty Python",
            },
            {
                "quote": "I’m not a Roman mum, I’m a kike, a yid, a heebie, "
                "a hook-nose, I’m kosher mum, I’m a Red Sea "
                "pedestrian, and proud of it!",
                "source": "Monty Python",
            },
            {
                "quote": "Our experts describe you as an appallingly dull fellow, "
                "unimaginative, timid, lacking in "
                "initiative, spineless, easily dominated, "
                "no sense of humour, tedious company and "
                "irrepressibly drab and awful.",
                "source": "Monty Python",
            },
            {
                "quote": "You don’t frighten us, English pig dogs. "
                "Go and boil your bottoms, you sons of a silly "
                "person. I blow my nose at you, so-called ‘Arthur King,’ "
                "you and all your silly "
                "English K-nig-hts.",
                "source": "Monty Python",
            },
            {
                "quote": "Every sperm is sacred, every sperm is great. "
                "If a sperm is wasted, God gets quite irate.",
                "source": "Monty Python",
            },
            {
                "quote": "Let the heathens spill theirs, on the dusty ground. "
                "God shall make them pay, for each "
                "sperm that can’t be found.",
                "source": "Monty Python",
            },
            {
                "quote": "I’m a lumberjack and I’m OK. "
                "I sleep all night and I work all day.",
                "source": "Monty Python",
            },
            {
                "quote": "I cut down trees, I eat my lunch, I go to the lavatory. "
                "On Wednesday I go shopping and have "
                "buttered scones for tea.",
                "source": "Monty Python",
            },
            {
                "quote": "We interrupt this program to annoy you and "
                "make things generally more irritating.",
                "source": "Monty Python",
            },
            {
                "quote": "He’s not the Messiah—he’s a very naughty boy!",
                "source": "Monty Python",
            },
            {
                "quote": "Strange women lying in ponds, distributing swords, "
                "is no basis for a system of government!",
                "source": "Monty Python",
            },
            {
                "quote": "Here are some completely gratuitous pictures of penises "
                "to annoy the censors and hopefully "
                "spark some sort of controversy.",
                "source": "Monty Python",
            },
            {
                "quote": "There’s no more work. We’re destitute. I’m afraid "
                "I have no choice but to sell you all for "
                "scientific experiments.",
                "source": "Monty Python",
            },
            {
                "quote": "They didn’t have their heads filled with all this "
                "Cartesian Dualism!",
                "source": "Monty Python",
            },
            {
                "quote": "You Americans, all you do is talk, and talk, "
                "and say ‘let me tell you something’ and "
                "‘I just wanna say.’ Well, you’re dead now, so shut up!",
                "source": "Monty Python",
            },
            {
                "quote": "Dew picked and flown from Iraq, cleansed in finest "
                "quality spring water, lightly killed, "
                "and then sealed in a succulent Swiss quintuple smooth treble "
                "cream milk chocolate envelope "
                "and lovingly frosted with glucose.",
                "source": "Monty Python",
            },
            {
                "quote": "There’s nothing wrong with you that an expensive "
                "operation can’t prolong.",
                "source": "Monty Python",
            },
            {
                "quote": "We’re right there with you, Mr. T.F. Gumby. "
                "Every time we watch the news, "
                "we want to moan ‘My brain huuuurts!’",
                "source": "Monty Python",
            },
            {
                "quote": "We serve no meat of any kind. We’re not only proud of that, "
                "we’re smug about it.",
                "source": "Monty Python",
            },
            {
                "quote": "Tonight, instead of discussing the existence or "
                "non-existence of God, "
                "they have decided to fight for it.",
                "source": "Monty Python",
            },
            {"quote": "She’s a witch! Burn her already!", "source": "Monty Python"},
            {
                "quote": "It’s just gone eight o’clock and time for the penguin "
                "on top of "
                "your television set to explode.",
                "source": "Monty Python",
            },
            {
                "quote": "When you’re walking home tonight and "
                "some great homicidal maniac comes "
                "after you with a bunch of loganberries, "
                "don’t come crying to me!",
                "source": "Monty Python",
            },
            {
                "quote": "Oh! Now we see the violence inherent in the system! Help, "
                "help, I’m being repressed!",
                "source": "Monty Python",
            },
            {
                "quote": "The medicine, education, wine, public order, irrigation, "
                "roads, the fresh-water system, "
                "and public health, what have the Romans ever done for us?",
                "source": "Monty Python",
            },
            {
                "quote": "It’s passed on! This parrot is no more! It has ceased to be! "
                "It’s expired and "
                "gone to meet its maker! This is a late parrot! It’s a stiff! "
                "Bereft of life, "
                "it rests in peace! If you hadn’t nailed it to the perch, "
                "it would be pushing up the daisies! "
                "It’s rung down the curtain and joined the choir invisible. "
                "This is an ex-parrot!",
                "source": "Monty Python",
            },
            {
                "quote": "There are a great many people in the country today, "
                "who through no fault of their own, are sane.",
                "source": "Monty Python",
            },
            {
                "quote": "Let’s not bicker and argue over who killed who.",
                "source": "Monty Python",
            },
            {
                "quote": "I’d like to complain about people who constantly hold "
                "things up by complaining about people who complain. "
                "It’s high time something was done about it!",
                "source": "Monty Python",
            },
            {
                "quote": "Are you suggesting that coconuts migrate?",
                "source": "Monty Python",
            },
            {"quote": "It’s just a flesh wound.", "source": "Monty Python"},
            {
                "quote": "Supreme executive power derives from a mandate from the "
                "masses, not from "
                "some farcical aquatic ceremony.",
                "source": "Monty Python",
            },
            {
                "quote": "Kilimanjaro is a pretty tricky climb you know, most of its "
                "up until you reach the very "
                "very top, and then it tends to slope away rather sharply.",
                "source": "Monty Python",
            },
            {
                "quote": "I fart in your general direction. "
                "Your mother was a hamster and your "
                "father smelt of elderberries.",
                "source": "Monty Python",
            },
            {
                "quote": "What… is the air-speed velocity of an unladen swallow?",
                "source": "Monty Python",
            },
            {"quote": "We are the Knights who say… NI.", "source": "Monty Python"},
            {
                "quote": "You must cut down the mightiest tree in the "
                "forest… WITH… A HERRING!",
                "source": "Monty Python",
            },
            {
                "quote": "Look, that rabbit’s got a vicious streak a mile wide! "
                "It’s a killer!",
                "source": "Monty Python",
            },
            {
                "quote": "O Knights of Ni, you are just and fair, and we will "
                "return with a shrubbery.",
                "source": "Monty Python",
            },
            {
                "quote": "Nobody expects the Spanish Inquisition!",
                "source": "Monty Python",
            },
            {
                "quote": "I cut down trees, I skip and jump, "
                "I like to press wild flowers. "
                "I put on women’s clothing and hang around in bars.",
                "source": "Monty Python",
            },
            {"quote": "My hovercraft is full of eels.", "source": "Monty Python"},
            {
                "quote": "Bally Jerry pranged his kite right in the how’s-your-father; "
                "hairy blighter, dicky-birded, "
                "feathered back on his sammy, took a waspy, "
                "flipped over on his Betty Harpers "
                "and caught his can in the Bertie.",
                "source": "Monty Python",
            },
            {
                "quote": "Do you want to come back to my place, bouncy bouncy?",
                "source": "Monty Python",
            },
        ]

    def get_quote(self):
        return self.quotes[secrets.randbelow(len(self.quotes))]

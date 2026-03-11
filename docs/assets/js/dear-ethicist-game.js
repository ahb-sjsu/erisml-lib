/* ==========================================================================
   Dear Ethicist — Interactive Game
   Full in-browser version with data collection for SQND research
   ========================================================================== */

(function () {
  'use strict';

  // =========================================================================
  // LETTER DATA (68 engineered probe letters)
  // =========================================================================
  var LETTERS = [{"id":"gate_promise_baseline","subject":"Friend promised to help me move","body":"Dear Ethicist,\n\nMy friend Taylor promised to help me move apartments this Saturday. We agreed on this three weeks ago.\n\nCan I count on Taylor showing up? Am I entitled to expect Taylor to follow through?","signoff":"EXPECTING IN ERIE","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Taylor","role":"friend","expected":"O"}],"questions":["Can I count on Taylor showing up?","Am I entitled to expect Taylor to follow through?"]},{"id":"gate_promise_level3","subject":"Friend mentioned work stress before helping","body":"Dear Ethicist,\n\nMy friend Taylor promised to help me move this Saturday. Yesterday Taylor mentioned having a really stressful week at work.\n\nCan I still count on Taylor? Do they still owe me their help despite the stress?","signoff":"STILL HOPEFUL","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Taylor","role":"friend","expected":"O"}],"questions":["Can I still count on Taylor?","Do they still owe me their help?"]},{"id":"gate_promise_level5","subject":"Friend said \"only if convenient\"","body":"Dear Ethicist,\n\nMy friend Taylor promised to help me move this Saturday. But yesterday Taylor texted \"I'll help if it's convenient for me, no pressure!\" with a smiley face.\n\nDoes that caveat release Taylor from the promise? Can I still expect them to show up?","signoff":"UNCERTAIN IN UTAH","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Taylor","role":"friend","expected":"L"}],"questions":["Does the caveat release Taylor?","Can I still expect them to show up?"]},{"id":"gate_promise_level6","subject":"Friend found someone else who might help","body":"Dear Ethicist,\n\nMy friend Taylor promised to help me move this Saturday. Yesterday Taylor mentioned \"I found a friend who might be able to help you too.\"\n\nDoes finding a potential replacement change Taylor's obligation? Can I still expect Taylor specifically to show up?","signoff":"COVERED IN COLORADO","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Taylor","role":"friend","expected":"O"}],"questions":["Does finding a replacement change the obligation?","Can I still expect Taylor specifically?"]},{"id":"gate_loan_baseline","subject":"Friend borrowed money six months ago","body":"Dear Ethicist,\n\nI lent my friend $300 six months ago. They said they'd pay me back \"soon.\"\n\nDo they still owe me this money? Is it rude for me to ask about it?","signoff":"WAITING ON WALNUT","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Friend","role":"borrower","expected":"O"}],"questions":["Do they still owe me this money?","Is it rude to ask about it?"]},{"id":"gate_loan_level5","subject":"Friend said \"consider it a gift if you want\"","body":"Dear Ethicist,\n\nI lent my friend $300 six months ago. When I mentioned it recently, they said \"Oh, consider it a gift if you want\u2014whatever works for you!\"\n\nDid that statement release them from the debt? Can I still ask for my money back?","signoff":"GENEROUS OR GULLIBLE","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Friend","role":"borrower","expected":"L"}],"questions":["Did that release them from the debt?","Can I still ask for my money back?"]},{"id":"corr_borrow_lender","subject":"Lent my drill, still waiting","body":"Dear Ethicist,\n\nI lent my neighbor my power drill two months ago. They haven't returned it and I haven't asked for it back.\n\nDo they have an obligation to return it proactively? Do I have a right to demand it back even though I haven't said anything?","signoff":"PATIENT ON PINE","parties":[{"name":"Neighbor","role":"borrower","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they have an obligation to return it?","Do I have a right to demand it back?"]},{"id":"corr_borrow_borrower","subject":"Borrowed a drill, haven't returned it","body":"Dear Ethicist,\n\nI borrowed my neighbor's power drill two months ago. I haven't returned it yet, and they haven't asked for it back.\n\nDo I have an obligation to return it proactively? Do they have a right to expect me to return it without asking?","signoff":"FORGETFUL ON FOURTH","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Neighbor","role":"lender","expected":"C"}],"questions":["Do I have an obligation to return it?","Do they have a right to expect it back?"]},{"id":"corr_favor_asker","subject":"Asked a favor, they said maybe","body":"Dear Ethicist,\n\nI asked my coworker to cover my shift next Friday for my daughter's recital. They said \"I'll try to make it work.\"\n\nDid that create an obligation on their part? Do I have a right to count on them?","signoff":"HOPEFUL FOR HELP","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Coworker","role":"colleague","expected":"L"}],"questions":["Did that create an obligation?","Do I have a right to count on them?"]},{"id":"corr_favor_asked","subject":"Said maybe to a favor request","body":"Dear Ethicist,\n\nMy coworker asked me to cover their shift next Friday for their daughter's recital. I said \"I'll try to make it work.\"\n\nDid that create an obligation on my part? Do they have a right to count on me now?","signoff":"ON THE FENCE","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Coworker","role":"colleague","expected":"N"}],"questions":["Did that create an obligation on my part?","Do they have a right to count on me?"]},{"id":"corr_secret_keeper","subject":"Friend told me a secret","body":"Dear Ethicist,\n\nMy friend told me about their marital problems and explicitly asked me to keep it secret. Now mutual friends are asking me what's wrong.\n\nAm I obligated to keep this secret? Does my friend have the right to expect my silence even when directly asked?","signoff":"KEEPER OF CONFIDENCES","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Friend","role":"confider","expected":"C"}],"questions":["Am I obligated to keep this secret?","Does my friend have the right to expect my silence?"]},{"id":"corr_secret_confider","subject":"Told a friend my secret","body":"Dear Ethicist,\n\nI told my friend about my marital problems and explicitly asked them to keep it secret. Now I'm hearing from others that they're asking questions.\n\nIs my friend obligated to keep my secret? Do I have the right to expect their silence even under social pressure?","signoff":"WORRIED ABOUT LEAKS","parties":[{"name":"Friend","role":"keeper","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Is my friend obligated to keep my secret?","Do I have the right to expect their silence?"]},{"id":"path_moving_helper","subject":"Promised to help friend move, but stressed","body":"Dear Ethicist,\n\nI promised to help my friend Alex move apartments this Saturday. But since then, I've had a brutal week at work and I'm exhausted. I also found someone who might be able to help Alex instead.\n\nDo I still have to show up? Or do the changed circumstances release me?","signoff":"STRESSED BUT COMMITTED","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Alex","role":"friend","expected":"C"}],"questions":["Do I still have to show up?","Do the circumstances release me?"]},{"id":"path_moving_helped","subject":"Friend promised to help me move","body":"Dear Ethicist,\n\nMy friend Jordan promised to help me move apartments this Saturday. But Jordan's been stressed at work and mentioned finding someone else who might help me instead.\n\nCan I still count on Jordan specifically? Do they still owe me their help, or have circumstances released them?","signoff":"LEFT HANGING","parties":[{"name":"Jordan","role":"friend","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Can I still count on Jordan?","Do they still owe me their help?"]},{"id":"path_wedding_guest","subject":"RSVPed yes but circumstances changed","body":"Dear Ethicist,\n\nI RSVPed \"yes\" to my cousin's wedding three months ago. Since then, my relationship with them has deteriorated due to an unrelated family conflict. The wedding is in two weeks.\n\nAm I obligated to attend since I said yes? Can I back out given the changed relationship?","signoff":"RELUCTANT RSVP","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Cousin","role":"relative","expected":"C"}],"questions":["Am I obligated to attend?","Can I back out?"]},{"id":"path_wedding_host","subject":"Cousin RSVPed but we've had conflict","body":"Dear Ethicist,\n\nMy cousin RSVPed \"yes\" to my wedding three months ago. Since then, we've had a falling out over an unrelated family matter. The wedding is in two weeks.\n\nDo I have the right to expect them to honor their RSVP? Or has our conflict released them from the commitment?","signoff":"COUNTING HEADS","parties":[{"name":"Cousin","role":"relative","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do I have the right to expect them to honor their RSVP?","Has our conflict released them?"]},{"id":"context_neighbor_neutral","subject":"Neighbor's noise at night","body":"Dear Ethicist,\n\nMy neighbor has been making noise late at night that wakes me up. I've mentioned it once and they said they'd try to be quieter, but it's continued.\n\nDo they have an obligation to keep the noise down? Do I have a right to quiet enjoyment of my home?","signoff":"SLEEPY IN SEATTLE","parties":[{"name":"Neighbor","role":"neighbor","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they have an obligation to keep noise down?","Do I have a right to quiet enjoyment?"]},{"id":"context_neighbor_sympathetic","subject":"Widow neighbor's noise at night","body":"Dear Ethicist,\n\nMy elderly neighbor, who recently lost her husband, has been making noise late at night that wakes me up. I think she can't sleep and watches TV loudly. I mentioned it once and she apologized tearfully, but it's continued.\n\nDo I have a right to demand quiet? Or does her grief change the equation?","signoff":"TORN NEXT DOOR","parties":[{"name":"Neighbor","role":"neighbor","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do I have a right to demand quiet?","Does her grief change the equation?"]},{"id":"context_neighbor_unsympathetic","subject":"Partying neighbor's noise at night","body":"Dear Ethicist,\n\nMy neighbor throws loud parties every weekend that keep me up until 3am. I've complained twice. They told me to \"lighten up\" and the parties continue.\n\nDo they have an obligation to respect quiet hours? Do I have a right to peace in my own home?","signoff":"FED UP ON FIFTH","parties":[{"name":"Neighbor","role":"neighbor","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they have an obligation to respect quiet hours?","Do I have a right to peace?"]},{"id":"phase_debt_clear","subject":"Written promise to repay","body":"Dear Ethicist,\n\nMy friend borrowed $500 and signed a note promising to repay by December 1st. It's now January 15th. No payment, no mention of it.\n\nDo they owe me this money? Do I have a right to demand repayment?","signoff":"CLEAR ON THE CONTRACT","parties":[{"name":"Friend","role":"borrower","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they owe me this money?","Do I have a right to demand repayment?"]},{"id":"phase_debt_moderate","subject":"Verbal promise to repay","body":"Dear Ethicist,\n\nMy friend borrowed $500 and verbally promised to \"pay me back soon.\" That was three months ago. We haven't discussed it since.\n\nDo they still owe me? Do I have a right to bring it up?","signoff":"SOMEWHAT CERTAIN","parties":[{"name":"Friend","role":"borrower","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they still owe me?","Do I have a right to bring it up?"]},{"id":"phase_debt_ambiguous","subject":"Unclear if it was a loan","body":"Dear Ethicist,\n\nI gave my friend $500 when they were in a tough spot. They said \"thanks, I'll make it up to you.\" I'm not sure if that meant they'd pay me back or just do something nice later.\n\nDo they owe me $500? Or was this a gift with vague reciprocity expectations?","signoff":"CONFUSED ABOUT CASH","parties":[{"name":"Friend","role":"recipient","expected":null},{"name":"You","role":"letter_writer","expected":null}],"questions":["Do they owe me $500?","Was this a gift or a loan?"]},{"id":"phase_debt_very_ambiguous","subject":"Was it a loan or a gift or neither?","body":"Dear Ethicist,\n\nMy friend mentioned needing money. I said \"I can help\" and transferred $500. They said \"you're the best.\" Did they think it was a gift? Did I think it was a loan? I honestly don't remember.\n\nIs there any obligation here? Does anyone have any rights?","signoff":"TOTALLY UNSURE","parties":[{"name":"Friend","role":"recipient","expected":null},{"name":"You","role":"letter_writer","expected":null}],"questions":["Is there any obligation here?","Does anyone have any rights?"]},{"id":"bias_omission_action","subject":"I caused harm by doing something","body":"Dear Ethicist,\n\nI was asked to water my neighbor's plants while they were away. I agreed. Then I forgot and actively decided not to go over because I was busy. The plants died.\n\nDo I owe them for the plants? Am I obligated to make this right?","signoff":"ACTIVE AGENT","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Neighbor","role":"neighbor","expected":"C"}],"questions":["Do I owe them for the plants?","Am I obligated to make this right?"]},{"id":"bias_omission_inaction","subject":"I caused harm by not doing something","body":"Dear Ethicist,\n\nMy neighbor asked me to water their plants while they were away. I said yes, then just... forgot. I never actively decided not to do it; it slipped my mind completely. The plants died.\n\nDo I owe them for the plants? Am I obligated to make this right?","signoff":"PASSIVE BYSTANDER","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Neighbor","role":"neighbor","expected":"C"}],"questions":["Do I owe them for the plants?","Am I obligated to make this right?"]},{"id":"bias_identifiable_named","subject":"Friend's specific child needs help","body":"Dear Ethicist,\n\nMy friend's daughter Emma, age 7, needs an expensive medical procedure. My friend asked if I could contribute $500 to help. I have the money but it would mean skipping my vacation.\n\nAm I obligated to help Emma specifically? Does my friend have a right to expect this?","signoff":"HEART STRINGS","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Friend","role":"parent","expected":null}],"questions":["Am I obligated to help?","Does my friend have a right to expect this?"]},{"id":"bias_identifiable_statistical","subject":"Charity request for children's hospital","body":"Dear Ethicist,\n\nA friend asked me to donate $500 to a children's hospital that helps kids needing expensive medical procedures. I have the money but it would mean skipping my vacation.\n\nAm I obligated to donate? Does my friend have a right to expect this?","signoff":"RATIONALLY REMOVED","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Friend","role":"requester","expected":null}],"questions":["Am I obligated to donate?","Does my friend have a right to expect this?"]},{"id":"bias_ingroup_family","subject":"Sister needs a ride to airport","body":"Dear Ethicist,\n\nMy sister asked me to drive her to the airport at 5am. It's a 45-minute drive each way. I have work the next day and it would mean losing significant sleep.\n\nAm I obligated to help my sister? Does she have a right to expect this from me?","signoff":"FAMILY FIRST","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Sister","role":"sibling","expected":"C"}],"questions":["Am I obligated to help my sister?","Does she have a right to expect this?"]},{"id":"bias_ingroup_acquaintance","subject":"Acquaintance needs a ride to airport","body":"Dear Ethicist,\n\nA coworker I barely know asked me to drive them to the airport at 5am. It's a 45-minute drive each way. I have work the next day and it would mean losing significant sleep.\n\nAm I obligated to help this person? Do they have a right to expect this from me?","signoff":"DISTANT DRIVER","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Coworker","role":"acquaintance","expected":"N"}],"questions":["Am I obligated to help this person?","Do they have a right to expect this?"]},{"id":"bias_reciprocity_owed","subject":"They helped me, now they need help","body":"Dear Ethicist,\n\nLast year my friend spent two days helping me move, refusing any payment. Now they're asking me to help them with a home renovation project that would take a full weekend.\n\nAm I obligated to help given what they did for me? Do they have a right to expect my help?","signoff":"PAYBACK TIME","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Friend","role":"friend","expected":"C"}],"questions":["Am I obligated to help?","Do they have a right to expect my help?"]},{"id":"bias_reciprocity_not_owed","subject":"Friend needs help but there's no history","body":"Dear Ethicist,\n\nA friend is asking me to help them with a home renovation project that would take a full weekend. We've never exchanged favors like this before.\n\nAm I obligated to help just because we're friends? Do they have a right to expect my help?","signoff":"CLEAN SLATE","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Friend","role":"friend","expected":"N"}],"questions":["Am I obligated to help?","Do they have a right to expect my help?"]},{"id":"bias_role_professional","subject":"Client asks for personal advice","body":"Dear Ethicist,\n\nI'm a financial advisor. A client going through a divorce asked me to recommend a divorce lawyer. This is clearly outside my professional scope.\n\nAm I obligated to help with this request? Does my client have a right to expect personal assistance beyond financial matters?","signoff":"PROFESSIONAL BOUNDARIES","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Client","role":"client","expected":"N"}],"questions":["Am I obligated to help with this?","Does my client have a right to expect this?"]},{"id":"bias_role_personal","subject":"Friend asks for professional help","body":"Dear Ethicist,\n\nI'm a financial advisor. A close friend going through a divorce asked me for financial advice about splitting assets. This would normally be a paid professional service.\n\nAm I obligated to help for free since we're friends? Does our friendship give them a right to my professional expertise?","signoff":"FRIENDLY ADVICE","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Friend","role":"friend","expected":null}],"questions":["Am I obligated to help for free?","Does our friendship give them a right to my expertise?"]},{"id":"contrary_exclusive_duties","subject":"Two promises, can only keep one","body":"Dear Ethicist,\n\nI promised to help my sister move on Saturday. I also promised to help my best friend with their wedding prep on the same day. I genuinely forgot when I made the second promise.\n\nAm I obligated to keep both promises? Is one person's claim stronger than the other's? Or am I free to choose since I can't do both?","signoff":"PULLED IN TWO DIRECTIONS","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Sister","role":"sibling","expected":null},{"name":"Friend","role":"friend","expected":null}],"questions":["Am I obligated to keep both promises?","Is one claim stronger than the other?"]},{"id":"contrary_freedom_vs_duty","subject":"Did I commit or just express interest?","body":"Dear Ethicist,\n\nWhen my friend was planning their party, I said \"sounds fun, I'd love to come!\" Now they're treating it like a firm commitment and planned around my attendance.\n\nDid my enthusiasm create an obligation to attend? Or am I still free to skip it if something else comes up?","signoff":"FREE OR BOUND","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Friend","role":"host","expected":null}],"questions":["Did my enthusiasm create an obligation?","Am I still free to skip it?"]},{"id":"compound_gate_correlative","subject":"Promise with caveat, from both perspectives","body":"Dear Ethicist,\n\nMy neighbor promised to walk my dog while I'm away, but added \"unless something comes up.\" Something came up for them. But I also found a backup dog-walker just in case.\n\nIs my neighbor released from their promise? Do I have grounds to be upset? And did my finding a backup affect their obligation in the first place?","signoff":"DOUBLY CONFUSED","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Neighbor","role":"neighbor","expected":null}],"questions":["Is my neighbor released from their promise?","Do I have grounds to be upset?","Did my finding a backup change things?"]},{"id":"compound_context_path","subject":"Changed circumstances and changed perspectives","body":"Dear Ethicist,\n\nMy brother-in-law borrowed $5000 for his business three years ago, promising to repay when profitable. The business succeeded, but then my sister (his wife) divorced him. Now he's my EX-brother-in-law.\n\nDoes he still owe me the money? Does our changed relationship affect the obligation? Would it be different if my sister had cheated on him versus him cheating on her?","signoff":"MANY LAYERS DEEP","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Ex-brother-in-law","role":"former_relative","expected":"O"}],"questions":["Does he still owe me the money?","Does our changed relationship affect the obligation?","Would the reason for divorce matter?"]},{"id":"corr_debt","subject":"I borrowed something and haven't returned it","body":"Dear Ethicist,\n\nI borrowed my neighbor's lawn mower two months ago. I haven't returned it yet, and they haven't asked for it back.\n\nTwo questions: Do I actually need to return it proactively? And does my neighbor have a right to demand it back even though they haven't said anything?","signoff":"FORGETFUL ON FIFTH STREET","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Neighbor","role":"lender","expected":"C"}],"questions":["Do I need to return it proactively?","Does my neighbor have a right to demand it back?"]},{"id":"corr_thesis","subject":"Sister demanding I proofread her thesis","body":"Dear Ethicist,\n\nI promised to proofread my sister's thesis. She's now demanding I drop everything to do it this weekend because her deadline moved up.\n\nWho's right here? Do I actually owe her this on her timeline? Does she have a right to demand it immediately?","signoff":"TORN BETWEEN PAGES","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Sister","role":"promisee","expected":"C"}],"questions":["Do I owe her this on her timeline?","Does she have a right to demand it immediately?"]},{"id":"corr_permission","subject":"Friend said I could use their car 'whenever'","body":"Dear Ethicist,\n\nMy friend told me I could use their car \"whenever I need it.\" I've been using it most weekends. Now they seem annoyed.\n\nAm I free to keep using it as promised? Can they suddenly demand I stop when they said \"whenever\"?","signoff":"BORROWER IN BROOKLYN","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Friend","role":"car_owner","expected":"N"}],"questions":["Am I free to keep using it?","Can they demand I stop?"]},{"id":"corr_stranger","subject":"Stranger struggling with groceries","body":"Dear Ethicist,\n\nI walked past a stranger struggling to carry groceries to their car. I didn't help because I was in a rush. Now I feel guilty.\n\nDid I actually have an obligation to help? Did they have any right to expect help from a random passerby?","signoff":"GUILTY BYSTANDER","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Stranger","role":"stranger","expected":"N"}],"questions":["Did I have an obligation to help?","Did they have a right to expect help?"]},{"id":"corr_loan","subject":"Friend hasn't paid me back","body":"Dear Ethicist,\n\nI lent my friend $200 six months ago. They said they'd pay me back \"soon\" but haven't mentioned it since. I feel awkward bringing it up.\n\nDo they still owe me this money? Do I have the right to ask for it back, or would that be rude?","signoff":"WAITING FOR REPAYMENT","parties":[{"name":"Friend","role":"borrower","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they still owe me this money?","Do I have the right to ask for it back?"]},{"id":"corr_secret","subject":"Friend told me something in confidence","body":"Dear Ethicist,\n\nMy friend told me a secret about their relationship troubles, explicitly asking me not to tell anyone. Now our mutual friends are asking me what's wrong with them.\n\nAm I obligated to keep this secret? Does my friend have the right to expect my silence even when directly asked?","signoff":"KEEPER OF SECRETS","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Friend","role":"confider","expected":"C"}],"questions":["Am I obligated to keep this secret?","Does my friend have the right to expect my silence?"]},{"id":"gate_L0_move","subject":"My friend promised to help me move","body":"Dear Ethicist,\n\nMy friend Morgan promised to help me move apartments this Saturday. We agreed on this three weeks ago, and Morgan confirmed with \"I'll be there at 8am!\"\n\nThe move is in two days. Do I have a right to expect Morgan to actually show up?","signoff":"COUNTING ON A FRIEND","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Morgan","role":"friend","expected":"O"}],"questions":["Do I have a right to expect Morgan to show up?"]},{"id":"gate_L5_move","subject":"Promise with a caveat","body":"Dear Ethicist,\n\nMy friend Morgan promised to help me move apartments this Saturday. We agreed on this three weeks ago. But yesterday Morgan texted me saying \"I'll help if it's convenient, no pressure!\" with a smiley face.\n\nNow I don't know if I can count on Morgan or not. Do I have a right to expect Morgan to show up? Or did that text release Morgan from the promise?","signoff":"CONFUSED IN CLEVELAND","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Morgan","role":"friend","expected":"L"}],"questions":["Do I have a right to expect Morgan to show up?","Did that text release Morgan from the promise?"]},{"id":"gate_L6_move","subject":"Friend mentioned finding someone else","body":"Dear Ethicist,\n\nMy friend Morgan promised to help me move apartments this Saturday. Yesterday Morgan mentioned \"I found a coworker who said they could help you too!\"\n\nDoes this mean Morgan is off the hook? Or does the original promise still stand?","signoff":"WONDERING IN WESTWOOD","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Morgan","role":"friend","expected":"O"}],"questions":["Does this mean Morgan is off the hook?"]},{"id":"gate_L8_release","subject":"I released my friend from a promise","body":"Dear Ethicist,\n\nMy friend Morgan promised to help me move. Yesterday I texted Morgan: \"Hey, I found professional movers. You're officially released from your promise! Enjoy your Saturday.\"\n\nMorgan seemed relieved. But now I'm second-guessing myself. Can I still expect Morgan to show up as a good friend, even though I released them?","signoff":"RELEASED IN RENO","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Morgan","role":"friend","expected":"L"}],"questions":["Can I still expect Morgan to show up?"]},{"id":"gate_L0_shift","subject":"Coworker promised to cover my shift","body":"Dear Ethicist,\n\nMy coworker Jamie promised to cover my shift next Friday so I could attend my daughter's recital. Jamie said \"Absolutely, I've got you covered!\"\n\nThe recital is in a week. Do I have a right to expect Jamie to follow through?","signoff":"RECITAL DAD","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Jamie","role":"coworker","expected":"O"}],"questions":["Do I have a right to expect Jamie to follow through?"]},{"id":"gate_L5_shift","subject":"Coworker's conditional promise","body":"Dear Ethicist,\n\nMy coworker Jamie promised to cover my shift, but yesterday said \"I'll do it if convenient, no guarantees.\"\n\nDo I have a right to expect Jamie to follow through? Or should I find backup?","signoff":"UNCERTAIN IN ACCOUNTING","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Jamie","role":"coworker","expected":"L"}],"questions":["Do I have a right to expect Jamie to follow through?"]},{"id":"gate_L3_dinner","subject":"Friend said they'd try to make dinner","body":"Dear Ethicist,\n\nI'm hosting a dinner party next weekend. My friend Sam said \"I'll try my best to be there, but work has been crazy.\"\n\nShould I count Sam as attending? Do I have a right to be upset if they don't show?","signoff":"HOPEFUL HOST","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Sam","role":"friend","expected":"O"}],"questions":["Should I count Sam as attending?","Do I have a right to be upset if they don't show?"]},{"id":"gate_L7_ambiguous","subject":"Not sure what my friend meant","body":"Dear Ethicist,\n\nMy friend promised to help me paint my apartment. Later they said \"Don't stress if you find someone else, I totally understand.\"\n\nIs that them backing out? Or just being considerate? I genuinely can't tell if I should still expect them.","signoff":"READING BETWEEN LINES","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Friend","role":"friend","expected":null}],"questions":["Is that them backing out?","Should I still expect them?"]},{"id":"family_wedding","subject":"Do I have to attend my cousin's wedding?","body":"Dear Ethicist,\n\nMy cousin is getting married across the country. We're not close - I see them maybe once every few years at family gatherings. The trip would cost me $1,500 and three days off work.\n\nMy mom insists I \"have to\" go because \"family is family.\" Do I actually have an obligation here? Does my cousin have any right to expect me there?","signoff":"RELUCTANT RELATIVE","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Cousin","role":"relative","expected":"N"}],"questions":["Do I have an obligation to attend?","Does my cousin have a right to expect me there?"]},{"id":"family_holiday","subject":"Mom expects me home for every holiday","body":"Dear Ethicist,\n\nMy mother expects me to come home for Thanksgiving, Christmas, AND Easter every year. I'm 34 and live four hours away. My partner's family never gets to see us.\n\nWhen I suggested alternating years, she said I was \"abandoning the family.\" Am I obligated to prioritize her holidays? Does she have the right to demand this?","signoff":"HOLIDAY HOSTAGE","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Mother","role":"parent","expected":"N"}],"questions":["Am I obligated to prioritize her holidays?","Does she have the right to demand this?"]},{"id":"family_eldercare","subject":"My siblings expect me to handle all of Dad's care","body":"Dear Ethicist,\n\nMy father needs daily assistance now. I live closest, so I've been doing everything - doctor visits, groceries, medication management. My two siblings live further away and contribute nothing.\n\nThey say since I'm \"right there\" it makes sense for me to handle it. But I'm exhausted. Do I have more obligation than them just because of geography? Do they have a right to opt out?","signoff":"OVERWHELMED IN OHIO","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Siblings","role":"family","expected":"O"}],"questions":["Do I have more obligation because I live closer?","Do my siblings have a right to opt out?"]},{"id":"family_loan","subject":"Brother wants another loan","body":"Dear Ethicist,\n\nMy brother has asked to borrow $5,000. I've lent him money three times before and he's never paid any of it back. He says \"family doesn't keep score.\"\n\nAm I obligated to help family when they ask? Does he have any right to expect this from me given his track record?","signoff":"FAMILY BANKER","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Brother","role":"sibling","expected":"N"}],"questions":["Am I obligated to help family when they ask?","Does he have any right to expect this?"]},{"id":"family_inheritance","subject":"Parents changed their will","body":"Dear Ethicist,\n\nMy parents recently told me they're leaving everything to my sister because \"she needs it more.\" I've worked hard and done well; she's made poor choices.\n\nI know it's their money, but I've been a dutiful child for 40 years. Do I have any claim here? Or do they have complete liberty to do what they want with their estate?","signoff":"WRITTEN OUT","parties":[{"name":"You","role":"letter_writer","expected":"N"},{"name":"Parents","role":"parents","expected":"L"}],"questions":["Do I have any claim to the inheritance?","Do they have complete liberty to distribute as they wish?"]},{"id":"work_overtime","subject":"Boss expects unpaid overtime","body":"Dear Ethicist,\n\nMy boss regularly expects me to stay late to finish projects, but I'm salaried so I don't get overtime pay. They say it's \"part of the job\" but it wasn't mentioned in my contract.\n\nAm I obligated to work beyond my scheduled hours? Does my employer have a right to expect this?","signoff":"BURNT OUT IN BOSTON","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Boss","role":"employer","expected":"N"}],"questions":["Am I obligated to work beyond my scheduled hours?","Does my employer have a right to expect this?"]},{"id":"work_reference","subject":"Asked to give a reference for a bad employee","body":"Dear Ethicist,\n\nA former employee who was mediocre at best asked me to be a reference for a new job. I can't honestly say good things, but I don't want to sabotage their career either.\n\nAm I obligated to give the reference since they asked? Do they have a right to expect my help?","signoff":"FORMER BOSS","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Former employee","role":"employee","expected":"N"}],"questions":["Am I obligated to give the reference?","Do they have a right to expect my help?"]},{"id":"work_cover","subject":"Coworker asked me to cover their mistake","body":"Dear Ethicist,\n\nMy coworker made a significant error on a project. They've asked me not to mention it in the team meeting and to help them fix it quietly. If it comes out, they could get fired.\n\nDo I have an obligation to cover for a colleague? Or do I owe honesty to my employer?","signoff":"TEAM PLAYER?","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Coworker","role":"colleague","expected":"N"}],"questions":["Do I have an obligation to cover for them?","Do I owe honesty to my employer?"]},{"id":"work_promotion","subject":"Promised promotion didn't happen","body":"Dear Ethicist,\n\nLast year my manager told me if I hit certain targets, I'd get promoted. I exceeded all of them. Now they say the budget doesn't allow for promotions this cycle.\n\nDid I have a valid claim to that promotion? Do they have the right to rescind what feels like a promise?","signoff":"PASSED OVER","parties":[{"name":"You","role":"letter_writer","expected":"C"},{"name":"Manager","role":"employer","expected":"O"}],"questions":["Did I have a valid claim to that promotion?","Do they have the right to rescind the promise?"]},{"id":"work_whistleblow","subject":"Should I report my company's violation?","body":"Dear Ethicist,\n\nI discovered my company is violating environmental regulations. Reporting it could cost people their jobs, including mine. Not reporting it means ongoing harm to the community.\n\nDo I have an obligation to report? Does the public have a claim on my honesty even if it costs me my livelihood?","signoff":"CONSCIENCE VS CAREER","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Public","role":"community","expected":"C"}],"questions":["Do I have an obligation to report?","Does the public have a claim on my honesty?"]},{"id":"friend_gossip","subject":"Friend told me about another friend's affair","body":"Dear Ethicist,\n\nMy friend Sarah told me that our mutual friend Jake is cheating on his wife. Sarah swore me to secrecy. But Jake's wife Emily is also my friend.\n\nAm I obligated to keep Sarah's secret? Does Emily have a right to know what I know? I feel terrible either way.","signoff":"STUCK IN THE MIDDLE","parties":[{"name":"You","role":"letter_writer","expected":null},{"name":"Emily","role":"friend","expected":null}],"questions":["Am I obligated to keep the secret?","Does Emily have a right to know?"]},{"id":"friend_bail","subject":"I committed but my situation changed","body":"Dear Ethicist,\n\nI agreed to be my friend's maid of honor six months ago. Since then, we've had a falling out over something unrelated. The wedding is in two months.\n\nCan I back out now? Or am I locked into this commitment despite our changed relationship?","signoff":"FLAKY FRIEND?","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Bride","role":"friend","expected":"C"}],"questions":["Can I back out now?","Am I locked into this commitment?"]},{"id":"neighbor_noise","subject":"Neighbor's dog barks all night","body":"Dear Ethicist,\n\nMy neighbor's dog barks from 11pm to 6am almost every night. I've mentioned it politely twice and they said they're \"working on it.\" It's been three months.\n\nDo they have an obligation to control their pet? Do I have a right to quiet enjoyment of my home?","signoff":"SLEEPLESS IN SEATTLE","parties":[{"name":"Neighbor","role":"neighbor","expected":"O"},{"name":"You","role":"letter_writer","expected":"C"}],"questions":["Do they have an obligation to control their pet?","Do I have a right to peace and quiet?"]},{"id":"neighbor_fence","subject":"Who pays for the fence between our properties?","body":"Dear Ethicist,\n\nThe fence between my property and my neighbor's is falling apart. They want to replace it with something nicer but expect me to pay half. I think the current fence is fine.\n\nAm I obligated to split the cost? Do they have the right to demand my contribution?","signoff":"ON THE BOUNDARY","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Neighbor","role":"neighbor","expected":"N"}],"questions":["Am I obligated to split the cost?","Do they have the right to demand my contribution?"]},{"id":"friend_honesty","subject":"Should I tell my friend their partner is cheating?","body":"Dear Ethicist,\n\nI saw my best friend's husband on what was clearly a date with another woman. My friend seems blissfully unaware.\n\nAm I obligated to tell them? Do they have a right to expect me to share what I saw?","signoff":"TRUTH TELLER","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Best friend","role":"friend","expected":"C"}],"questions":["Am I obligated to tell them?","Do they have a right to know?"]},{"id":"ex_stuff","subject":"Ex wants their stuff back after two years","body":"Dear Ethicist,\n\nMy ex left some boxes at my place when we broke up two years ago. I've asked multiple times if they want them. Now they suddenly demand I return everything immediately.\n\nAfter two years of ignoring my offers, do they still have a claim to this stuff? Am I obligated to accommodate their timeline?","signoff":"MOVING ON","parties":[{"name":"You","role":"letter_writer","expected":"L"},{"name":"Ex","role":"ex_partner","expected":"N"}],"questions":["Do they still have a claim to this stuff?","Am I obligated to accommodate their timeline?"]},{"id":"roommate_chores","subject":"Roommate deal about dinner","body":"Dear Ethicist,\n\nMy roommate and I have an informal deal: whoever gets home first orders dinner. Last Tuesday, I got home first but crashed on the couch after a brutal day. My roommate was annoyed.\n\nDo I actually owe her an apology? We never signed anything. Does our informal arrangement create a real obligation?","signoff":"COUCH POTATO IN QUEENS","parties":[{"name":"You","role":"letter_writer","expected":"O"},{"name":"Roommate","role":"roommate","expected":"C"}],"questions":["Do I owe her an apology?","Does an informal deal create real obligations?"]}];

  // Merge extra letters from separate file (if loaded)
  if (window.DEAR_ETHICIST_EXTRA) LETTERS = LETTERS.concat(window.DEAR_ETHICIST_EXTRA);

  var LETTERS_PER_SESSION = 10;

  // Google Sheets endpoint — set this after deploying the Apps Script
  // See: docs/site/assets/js/dear-ethicist-sheets-setup.md
  var SHEETS_ENDPOINT = '';  // e.g. 'https://script.google.com/macros/s/DEPLOY_ID/exec'

  // =========================================================================
  // REACTION TEMPLATES (ported from reactions.py)
  // =========================================================================
  var SUPPORTIVE = [
    "@{u}: Finally, someone with common sense!",
    "@{u}: This is exactly what I needed to hear.",
    "@{u}: You nailed it. Forwarding to my {r}.",
    "@{u}: 100% agree. Clear and fair.",
    "@{u}: The Ethicist speaks truth once again.",
  ];
  var CRITICAL = [
    "@{u}: Eh, I think you're being too harsh here.",
    "@{u}: Disagree. Life is more complicated than this.",
    "@{u}: Easy to say from the outside...",
    "@{u}: This advice would NOT work in the real world.",
    "@{u}: I expected more nuance from this column.",
  ];
  var MIXED = [
    "@{u}: I see both sides, but lean toward the opposite view.",
    "@{u}: Good points, though I'm not fully convinced.",
    "@{u}: Interesting take. My therapist would disagree.",
    "@{u}: Right answer, wrong reasoning?",
  ];
  var HUMOROUS = [
    "@{u}: Morgan/Jamie/whoever sounds like my ex lol",
    "@{u}: Can you answer my letter about whether I owe my cat an apology?",
    "@{u}: *takes notes for next family dinner*",
    "@{u}: The real question is why anyone promises anything ever",
  ];
  var USERNAMES = [
    "MidwestMom47", "DevilsAdvocate", "RealistRick", "HopefulHannah",
    "SkepticalSam", "WisdomSeeker", "TruthTeller99", "JustMyOpinion",
    "BeenThereDoneThat", "NeutralNancy", "FairIsFair", "CommonSense101",
    "PhilosophyMajor", "RealTalk", "ThinkingItThrough", "VoiceOfReason",
  ];
  var RELATIONS = ["sister", "brother", "friend", "coworker", "neighbor", "roommate"];

  // =========================================================================
  // UTILITY
  // =========================================================================
  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }
  function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function generateReactions(verdicts) {
    var matchesExpected = verdicts.every(function (v) {
      return v.expected === null || v.state === v.expected;
    });
    var weights = matchesExpected ? [35, 25, 25, 15] : [20, 35, 30, 15];
    var pools = [SUPPORTIVE, CRITICAL, MIXED, HUMOROUS];
    var used = {};
    var reactions = [];
    for (var i = 0; i < 3; i++) {
      var r = Math.random() * (weights[0] + weights[1] + weights[2] + weights[3]);
      var poolIdx = 0, cumul = 0;
      for (var k = 0; k < weights.length; k++) {
        cumul += weights[k];
        if (r < cumul) { poolIdx = k; break; }
      }
      var uname;
      do { uname = pick(USERNAMES); } while (used[uname] && Object.keys(used).length < USERNAMES.length);
      used[uname] = true;
      var text = pick(pools[poolIdx])
        .replace('{u}', uname)
        .replace('{r}', pick(RELATIONS));
      reactions.push({ text: text, tone: ['supportive', 'critical', 'mixed', 'humorous'][poolIdx] });
    }
    return reactions;
  }

  // =========================================================================
  // CONTEXTUAL OPTIONS (replaces abstract O/C/L/N with descriptions)
  // =========================================================================
  function detectScenario(letter) {
    var t = (letter.body + ' ' + letter.subject + ' ' + letter.id).toLowerCase();
    if (t.match(/move|moving|apartment/)) return 'move';
    if (t.match(/\$|borrow|lent|loan|repay|money|debt|pay.*back/)) return 'money';
    if (t.match(/secret|confiden/)) return 'secret';
    if (t.match(/noise|bark|loud|quiet|sleep/)) return 'noise';
    if (t.match(/wedding|rsvp/)) return 'wedding';
    if (t.match(/shift|cover.*shift|cover my|cover their/)) return 'shift';
    if (t.match(/proofread|thesis/)) return 'proofread';
    if (t.match(/drill|lawn.?mower/)) return 'borrow_item';
    if (t.match(/car.*whenever|use.*car/)) return 'car';
    if (t.match(/cheat|affair/)) return 'affair';
    if (t.match(/promot/)) return 'promotion';
    if (t.match(/overtime|stay late/)) return 'overtime';
    if (t.match(/reference|recommend/)) return 'reference';
    if (t.match(/report|whistleblow|violat/)) return 'whistleblow';
    if (t.match(/cover.*mistake|error.*project/)) return 'cover_mistake';
    if (t.match(/holiday|thanksgiv|christmas|easter/)) return 'holiday';
    if (t.match(/elder|care.*dad|father.*need|daily.*assist/)) return 'eldercare';
    if (t.match(/inherit|will|estate/)) return 'inheritance';
    if (t.match(/fence|property.*boundar/)) return 'fence';
    if (t.match(/plant|water.*plant/)) return 'plants';
    if (t.match(/roommate.*deal|chore|dinner.*deal/)) return 'roommate';
    if (t.match(/maid of honor/)) return 'commitment';
    if (t.match(/ex.*stuff|box.*broke/)) return 'ex_stuff';
    if (t.match(/stranger.*groceries|stranger.*struggle/)) return 'stranger_help';
    if (t.match(/stream|password|netflix|account.*ex/)) return 'digital';
    if (t.match(/photo|picture|image.*post|tag/)) return 'photo';
    if (t.match(/vaccine|treatment|medic|doctor|patient/)) return 'medical';
    if (t.match(/wallet|found.*\$/)) return 'found';
    if (t.match(/park.*spot|parking/)) return 'parking';
    if (t.match(/credit.*idea|taking credit/)) return 'credit';
    if (t.match(/ghost|ghosted/)) return 'ghosting';
    if (t.match(/wifi|internet/)) return 'wifi';
    if (t.match(/landlord|tenant|rent/)) return 'landlord';
    if (t.match(/train.*replacement|replac.*me/)) return 'replacement';
    if (t.match(/promis|commit|agreed/)) return 'promise';
    if (t.match(/help|favor|assist/)) return 'help';
    if (t.match(/invite|party|dinner|attend/)) return 'attendance';
    return 'general';
  }

  function getPartyContext(party, letter) {
    var scenario = detectScenario(letter);
    var role = party.role;
    var other = null;
    for (var i = 0; i < letter.parties.length; i++) {
      if (letter.parties[i].name !== party.name) { other = letter.parties[i]; break; }
    }
    var oN = other ? (other.name === 'You' ? 'you' : other.name) : 'the other person';

    // Role-specific contexts
    var R = {
      borrower:    { duty: 'return what was borrowed', claim: 'patience from ' + oN },
      recipient:   { duty: 'acknowledge the gift', claim: 'support from ' + oN },
      lender:      { duty: 'be reasonable about timing', claim: 'repayment from ' + oN },
      confider:    { duty: 'handle this carefully', claim: 'confidentiality from ' + oN },
      keeper:      { duty: 'keep the secret', claim: 'understanding from ' + oN },
      car_owner:   { duty: 'honor what was offered', claim: 'respect from ' + oN },
      community:   { duty: 'address the situation', claim: 'someone to report the harm' },
      stranger:    { duty: 'accept the situation', claim: 'help from passersby' },
      employer:    { duty: 'fulfill workplace promises', claim: 'performance from ' + oN },
      promisee:    { duty: 'be understanding', claim: 'the promise honored by ' + oN },
      ex_partner:  { duty: 'handle the breakup fairly', claim: 'respect from ' + oN },
    };
    if (R[role]) return R[role];

    // Scenario-based contexts
    var S = {
      move:          { duty: 'help with the move', claim: 'help from ' + oN },
      money:         { duty: 'handle the money fairly', claim: 'repayment from ' + oN },
      secret:        { duty: 'keep the confidence', claim: 'the secret kept by ' + oN },
      noise:         { duty: 'keep things quiet', claim: 'peace and quiet from ' + oN },
      wedding:       { duty: 'attend as committed', claim: 'attendance from ' + oN },
      shift:         { duty: 'cover the shift', claim: 'coverage from ' + oN },
      proofread:     { duty: 'do the proofreading', claim: 'the proofreading from ' + oN },
      borrow_item:   { duty: 'return the item', claim: 'the item back from ' + oN },
      car:           { duty: 'respect the arrangement', claim: 'continued access' },
      affair:        { duty: 'be honest about this', claim: 'the truth from ' + oN },
      promotion:     { duty: 'deliver what was promised', claim: 'the promised promotion' },
      overtime:      { duty: 'put in extra time', claim: 'fair treatment from ' + oN },
      reference:     { duty: 'provide an honest reference', claim: 'a reference from ' + oN },
      whistleblow:   { duty: 'report the problem', claim: 'honesty from ' + oN },
      cover_mistake: { duty: 'cover for a colleague', claim: 'honesty from ' + oN },
      holiday:       { duty: 'attend family events', claim: 'flexibility from ' + oN },
      eldercare:     { duty: 'help with caregiving', claim: 'fair sharing of care duties' },
      inheritance:   { duty: 'accept the decision', claim: 'a fair share' },
      fence:         { duty: 'contribute to the repair', claim: 'a contribution from ' + oN },
      plants:        { duty: 'water the plants', claim: 'the plants cared for' },
      roommate:      { duty: 'keep up the arrangement', claim: oN + ' pulling their weight' },
      commitment:    { duty: 'honor the commitment', claim: 'understanding from ' + oN },
      ex_stuff:      { duty: 'return belongings', claim: 'their belongings from ' + oN },
      stranger_help: { duty: 'help the person', claim: 'help from passersby' },
      promise:       { duty: 'keep the promise', claim: 'the promise honored' },
      help:          { duty: 'help as asked', claim: 'help from ' + oN },
      attendance:    { duty: 'show up as expected', claim: oN + "'s attendance" },
      digital:       { duty: 'respect digital boundaries', claim: 'privacy from ' + oN },
      photo:         { duty: 'ask before sharing', claim: 'consent from ' + oN },
      medical:       { duty: 'do what is best', claim: 'proper care from ' + oN },
      found:         { duty: 'return what was found', claim: 'honesty from the finder' },
      parking:       { duty: 'respect the space', claim: 'the parking spot' },
      credit:        { duty: 'give proper credit', claim: 'credit for the work' },
      ghosting:      { duty: 'communicate honestly', claim: 'a response from ' + oN },
      wifi:          { duty: 'respect others\' property', claim: 'network security from ' + oN },
      landlord:      { duty: 'respect the lease terms', claim: 'proper notice from ' + oN },
      replacement:   { duty: 'help with the transition', claim: 'fair treatment from ' + oN },
      general:       { duty: 'do the right thing here', claim: 'action from ' + oN },
    };
    return S[scenario] || S.general;
  }

  function getContextualOptions(party, letter) {
    var ctx = getPartyContext(party, letter);
    var n = party.name;
    var isYou = (n === 'You');
    var S = isYou ? 'I' : n;
    var h = isYou ? 'have' : 'has';
    var a = isYou ? "'m" : ' is';
    return [
      { pos: 'O', label: S + ' ' + h + ' a duty',  desc: S + ' must ' + ctx.duty },
      { pos: 'C', label: S + ' ' + h + ' a right', desc: S + ' can rightfully expect ' + ctx.claim },
      { pos: 'L', label: S + a + ' free to choose', desc: 'No obligation — ' + (isYou ? 'I' : n) + ' can decide either way' },
      { pos: 'N', label: S + ' ' + h + ' no claim', desc: S + " can't demand " + ctx.claim },
    ];
  }

  function positionName(pos) {
    return { O: 'Duty', C: 'Right', L: 'Freedom', N: 'No Claim' }[pos] || pos;
  }

  // =========================================================================
  // BOND INDEX CALCULATION
  // =========================================================================
  function isCorrelativePair(a, b) {
    return (a === 'O' && b === 'C') || (a === 'C' && b === 'O') ||
           (a === 'L' && b === 'N') || (a === 'N' && b === 'L');
  }

  function computeBondIndex(sessionVerdicts) {
    // Bond Index: fraction of letter pairs where correlative symmetry was violated
    var total = 0, violations = 0;
    sessionVerdicts.forEach(function (sv) {
      // For 2-party letters, check if the pair is correlative
      if (sv.verdicts.length === 2) {
        total++;
        if (!isCorrelativePair(sv.verdicts[0].state, sv.verdicts[1].state)) {
          violations++;
        }
      }
      // For 3+ party letters, check all consecutive pairs
      if (sv.verdicts.length > 2) {
        for (var i = 0; i < sv.verdicts.length - 1; i++) {
          total++;
          if (!isCorrelativePair(sv.verdicts[i].state, sv.verdicts[i + 1].state)) {
            violations++;
          }
        }
      }
    });
    return total > 0 ? violations / total : 0;
  }

  // =========================================================================
  // GAME STATE
  // =========================================================================
  var state = {
    phase: 'start',       // start | playing | reaction | summary
    sessionId: null,
    letters: [],           // shuffled subset
    currentIdx: 0,
    verdicts: [],          // per-party choices for current letter
    sessionHistory: [],    // all completed letter verdicts
    letterStartTime: null,
    allSessions: [],       // persisted across sessions
  };

  // Load prior sessions from localStorage
  try {
    var saved = localStorage.getItem('dearEthicist_sessions');
    if (saved) state.allSessions = JSON.parse(saved);
  } catch (e) { /* ignore */ }

  // =========================================================================
  // RENDERING
  // =========================================================================
  var root;

  function render() {
    if (!root) return;
    switch (state.phase) {
      case 'start': renderStart(); break;
      case 'playing': renderPlaying(); break;
      case 'reaction': renderReaction(); break;
      case 'summary': renderSummary(); break;
    }
  }

  function renderStart() {
    var totalPlayed = state.allSessions.reduce(function (s, sess) { return s + sess.letters.length; }, 0);
    root.innerHTML =
      '<div class="de-start">' +
        '<div class="de-newspaper-header">' +
          '<div class="de-np-rule"></div>' +
          '<div class="de-np-title">The Morning Chronicle</div>' +
          '<div class="de-np-subtitle">Advice Column</div>' +
          '<div class="de-np-rule"></div>' +
        '</div>' +
        '<div class="de-start-body">' +
          '<h3>Welcome, Ethicist.</h3>' +
          '<p>You are the advice columnist. Read letters from people facing everyday moral dilemmas, then judge each person\'s moral position:</p>' +
          '<div class="de-positions-legend">' +
            '<span class="de-pos de-pos-O">Duty <small>bound to act</small></span>' +
            '<span class="de-pos de-pos-C">Right <small>can expect action</small></span>' +
            '<span class="de-pos de-pos-L">Freedom <small>may choose</small></span>' +
            '<span class="de-pos de-pos-N">No Claim <small>can\'t demand</small></span>' +
          '</div>' +
          '<p class="de-hint">These come in pairs: <strong>Duty \u2194 Right</strong> and <strong>Freedom \u2194 No Claim</strong>. If someone has a duty, the other person has a right to expect it. Your <strong>Bond Index</strong> measures how consistently you pair them.</p>' +
          '<div class="de-start-stats">' +
            '<div class="de-ss"><span class="de-ss-num">' + LETTERS.length + '</span><span class="de-ss-label">Letters</span></div>' +
            '<div class="de-ss"><span class="de-ss-num">' + LETTERS_PER_SESSION + '</span><span class="de-ss-label">Per Session</span></div>' +
            '<div class="de-ss"><span class="de-ss-num">' + totalPlayed + '</span><span class="de-ss-label">You\'ve Played</span></div>' +
          '</div>' +
          '<button class="de-btn de-btn-primary" id="de-start-btn">Begin Session</button>' +
        '</div>' +
      '</div>';

    document.getElementById('de-start-btn').addEventListener('click', startSession);
  }

  function startSession() {
    state.sessionId = uuid();
    state.letters = shuffle(LETTERS).slice(0, LETTERS_PER_SESSION);
    state.currentIdx = 0;
    state.sessionHistory = [];
    state.verdicts = [];
    state.phase = 'playing';
    render();
  }

  function renderPlaying() {
    var letter = state.letters[state.currentIdx];
    state.letterStartTime = Date.now();
    state.verdicts = letter.parties.map(function () { return null; });

    var partySections = letter.parties.map(function (p, i) {
      var opts = getContextualOptions(p, letter);
      var cards = opts.map(function (opt) {
        return '<div class="de-option" data-pos="' + opt.pos + '" data-pidx="' + i + '">' +
          '<span class="de-option-dot"></span>' +
          '<div class="de-option-text">' +
            '<span class="de-option-label">' + escHtml(opt.label) + '</span>' +
            '<span class="de-option-desc">' + escHtml(opt.desc) + '</span>' +
          '</div>' +
        '</div>';
      }).join('');
      return '<div class="de-party-section">' +
        '<div class="de-party-q">What is <strong>' + escHtml(p.name) + '</strong>\'s position? <small>(' + escHtml(p.role.replace(/_/g, ' ')) + ')</small></div>' +
        '<div class="de-options">' + cards + '</div>' +
      '</div>';
    }).join('');

    root.innerHTML =
      '<div class="de-playing">' +
        '<div class="de-progress-bar"><div class="de-progress-fill" style="width:' + ((state.currentIdx / state.letters.length) * 100) + '%"></div></div>' +
        '<div class="de-letter-counter">Letter ' + (state.currentIdx + 1) + ' of ' + state.letters.length + '</div>' +
        '<div class="de-newspaper-header de-np-sm">' +
          '<div class="de-np-title">The Morning Chronicle</div>' +
          '<div class="de-np-subtitle">Advice Column</div>' +
        '</div>' +
        '<div class="de-letter">' +
          '<div class="de-letter-subj">' + escHtml(letter.subject) + '</div>' +
          '<div class="de-letter-body">' + escHtml(letter.body).replace(/\n/g, '<br>') + '</div>' +
          '<div class="de-letter-sig">&mdash; ' + escHtml(letter.signoff) + '</div>' +
        '</div>' +
        '<div class="de-classify">' +
          '<h4>Your verdict:</h4>' +
          partySections +
        '</div>' +
        '<button class="de-btn de-btn-primary de-publish-btn" id="de-publish" disabled>Publish Your Verdict</button>' +
      '</div>';

    // Wire up option cards
    root.querySelectorAll('.de-option').forEach(function (card) {
      card.addEventListener('click', function () {
        var idx = parseInt(card.dataset.pidx);
        var section = card.closest('.de-party-section');
        section.querySelectorAll('.de-option').forEach(function (c) { c.classList.remove('selected'); });
        card.classList.add('selected');
        state.verdicts[idx] = card.dataset.pos;
        var allSet = state.verdicts.every(function (v) { return v !== null; });
        document.getElementById('de-publish').disabled = !allSet;
      });
    });

    document.getElementById('de-publish').addEventListener('click', publishVerdict);
  }

  function publishVerdict() {
    var letter = state.letters[state.currentIdx];
    var elapsed = Math.round((Date.now() - state.letterStartTime) / 1000);

    var verdictData = {
      letter_id: letter.id,
      timestamp: new Date().toISOString(),
      time_spent_seconds: elapsed,
      verdicts: letter.parties.map(function (p, i) {
        return {
          party_name: p.name,
          party_role: p.role,
          state: state.verdicts[i],
          expected: p.expected,
        };
      }),
    };

    // Check correlative symmetry for 2-party letters
    if (verdictData.verdicts.length === 2) {
      verdictData.correlative_holds = isCorrelativePair(
        verdictData.verdicts[0].state,
        verdictData.verdicts[1].state
      );
    }

    // Generate reactions
    verdictData.reactions = generateReactions(verdictData.verdicts);

    state.sessionHistory.push(verdictData);
    state.phase = 'reaction';
    render();
  }

  function renderReaction() {
    var vd = state.sessionHistory[state.sessionHistory.length - 1];
    var letter = state.letters[state.currentIdx];
    var runningBI = computeBondIndex(state.sessionHistory);

    // Symmetry check display
    var symmetryHtml = '';
    if (vd.verdicts.length === 2) {
      var a = vd.verdicts[0].state, b = vd.verdicts[1].state;
      if (vd.correlative_holds) {
        symmetryHtml =
          '<div class="de-symmetry de-sym-good">' +
            '<strong>Consistent pairing:</strong> ' + positionName(a) + ' \u2194 ' + positionName(b) +
            ' \u2014 these naturally go together.' +
          '</div>';
      } else {
        symmetryHtml =
          '<div class="de-symmetry de-sym-warn">' +
            '<strong>Inconsistent pairing:</strong> ' + positionName(a) + ' \u2194 ' + positionName(b) +
            ' doesn\'t pair naturally. Duty goes with Right, and Freedom goes with No Claim.' +
          '</div>';
      }
    }

    // Verdict summary
    var verdictSummary = vd.verdicts.map(function (v) {
      return '<span class="de-verdict-chip"><strong>' + escHtml(v.party_name) + ':</strong> ' +
        '<span class="de-pos-tag de-pos-' + v.state + '">' + positionName(v.state) + '</span></span>';
    }).join('');

    // Reactions
    var reactionsHtml = vd.reactions.map(function (r) {
      var toneClass = 'de-react-' + r.tone;
      return '<div class="de-reaction ' + toneClass + '">' + escHtml(r.text) + '</div>';
    }).join('');

    var isLast = state.currentIdx >= state.letters.length - 1;
    var nextLabel = isLast ? 'See Your Results' : 'Next Letter \u2192';

    root.innerHTML =
      '<div class="de-reaction-phase">' +
        '<div class="de-progress-bar"><div class="de-progress-fill" style="width:' + (((state.currentIdx + 1) / state.letters.length) * 100) + '%"></div></div>' +
        '<div class="de-published-header">Your verdict has been published!</div>' +
        '<div class="de-verdict-summary">' + verdictSummary + '</div>' +
        symmetryHtml +
        '<div class="de-bond-index-live">' +
          '<span class="de-bi-label">Running Bond Index:</span>' +
          '<span class="de-bi-value ' + (runningBI === 0 ? 'de-bi-perfect' : runningBI < 0.3 ? 'de-bi-good' : 'de-bi-high') + '">' +
            runningBI.toFixed(3) +
          '</span>' +
        '</div>' +
        '<div class="de-reactions-section">' +
          '<h4>Reader Reactions</h4>' +
          reactionsHtml +
        '</div>' +
        '<button class="de-btn de-btn-primary" id="de-next">' + nextLabel + '</button>' +
      '</div>';

    document.getElementById('de-next').addEventListener('click', function () {
      if (isLast) {
        state.phase = 'summary';
      } else {
        state.currentIdx++;
        state.phase = 'playing';
      }
      render();
    });
  }

  function renderSummary() {
    var bi = computeBondIndex(state.sessionHistory);

    // Save session
    var sessionData = {
      session_id: state.sessionId,
      timestamp: new Date().toISOString(),
      bond_index: bi,
      letters: state.sessionHistory,
    };
    state.allSessions.push(sessionData);
    try {
      localStorage.setItem('dearEthicist_sessions', JSON.stringify(state.allSessions));
    } catch (e) { /* storage full */ }

    // Grade
    var grade, gradeClass, gradeDesc;
    if (bi === 0) {
      grade = 'Perfect'; gradeClass = 'de-grade-perfect';
      gradeDesc = 'Perfect consistency. Every duty paired with a right, every freedom with no claim.';
    } else if (bi < 0.2) {
      grade = 'Strong'; gradeClass = 'de-grade-good';
      gradeDesc = 'Strong consistency. Your pairings are nearly perfect with minor deviations.';
    } else if (bi < 0.5) {
      grade = 'Moderate'; gradeClass = 'de-grade-moderate';
      gradeDesc = 'Some inconsistencies. You may be applying different standards to different sides of the same dilemma.';
    } else {
      grade = 'Divergent'; gradeClass = 'de-grade-high';
      gradeDesc = 'Significant asymmetry. Your reasoning treats the same situation differently depending on perspective.';
    }

    // Per-letter breakdown
    var breakdownRows = state.sessionHistory.map(function (sv, i) {
      var letter = state.letters[i];
      var corr = sv.correlative_holds;
      var corrStr = corr === true ? '\u2713' : corr === false ? '\u2717' : '\u2014';
      var corrClass = corr === true ? 'de-check-good' : corr === false ? 'de-check-bad' : '';
      return '<tr>' +
        '<td>' + (i + 1) + '</td>' +
        '<td class="de-td-subj">' + escHtml(letter.subject) + '</td>' +
        '<td>' + sv.verdicts.map(function (v) { return positionName(v.state); }).join(', ') + '</td>' +
        '<td class="' + corrClass + '">' + corrStr + '</td>' +
        '<td>' + sv.time_spent_seconds + 's</td>' +
      '</tr>';
    }).join('');

    var totalSessions = state.allSessions.length;
    var totalLetters = state.allSessions.reduce(function (s, sess) { return s + sess.letters.length; }, 0);

    root.innerHTML =
      '<div class="de-summary">' +
        '<div class="de-summary-header">' +
          '<h3>Session Complete</h3>' +
          '<div class="de-bi-big ' + gradeClass + '">' +
            '<div class="de-bi-number">' + bi.toFixed(3) + '</div>' +
            '<div class="de-bi-grade">' + grade + '</div>' +
          '</div>' +
          '<p class="de-bi-desc">' + gradeDesc + '</p>' +
        '</div>' +
        '<div class="de-breakdown">' +
          '<h4>Letter Breakdown</h4>' +
          '<table class="de-table">' +
            '<thead><tr><th>#</th><th>Letter</th><th>Verdicts</th><th>Corr.</th><th>Time</th></tr></thead>' +
            '<tbody>' + breakdownRows + '</tbody>' +
          '</table>' +
        '</div>' +
        '<div class="de-cumulative">' +
          '<div class="de-ss"><span class="de-ss-num">' + totalSessions + '</span><span class="de-ss-label">Total Sessions</span></div>' +
          '<div class="de-ss"><span class="de-ss-num">' + totalLetters + '</span><span class="de-ss-label">Letters Played</span></div>' +
        '</div>' +
        (SHEETS_ENDPOINT ?
          '<div class="de-submit-section">' +
            '<button class="de-btn de-btn-submit" id="de-submit-research">Submit for Research (Anonymous)</button>' +
            '<p class="de-submit-note">Contributes your session to the SQND correlative symmetry dataset. No personal data is collected.</p>' +
          '</div>' : '') +
        '<div class="de-summary-actions">' +
          '<button class="de-btn de-btn-primary" id="de-play-again">Play Again</button>' +
          '<button class="de-btn de-btn-secondary" id="de-download">Download Session Data (JSON)</button>' +
          '<button class="de-btn de-btn-secondary" id="de-download-all">Download All Sessions</button>' +
        '</div>' +
      '</div>';

    document.getElementById('de-play-again').addEventListener('click', function () {
      state.phase = 'start';
      render();
    });

    document.getElementById('de-download').addEventListener('click', function () {
      downloadJSON(sessionData, 'dear-ethicist-session-' + state.sessionId.slice(0, 8) + '.json');
    });

    document.getElementById('de-download-all').addEventListener('click', function () {
      downloadJSON(state.allSessions, 'dear-ethicist-all-sessions.json');
    });

    var submitBtn = document.getElementById('de-submit-research');
    if (submitBtn) {
      submitBtn.addEventListener('click', function () {
        submitToSheets(sessionData);
      });
    }
  }

  function submitToSheets(sessionData) {
    if (!SHEETS_ENDPOINT) return;
    // Flatten: one row per letter verdict
    var rows = sessionData.letters.map(function (sv) {
      var v = sv.verdicts;
      return {
        session_id: sessionData.session_id,
        timestamp: sv.timestamp,
        letter_id: sv.letter_id,
        party_1_name: v[0] ? v[0].party_name : '',
        party_1_role: v[0] ? v[0].party_role : '',
        party_1_assigned: v[0] ? v[0].state : '',
        party_1_expected: v[0] ? (v[0].expected || '') : '',
        party_2_name: v[1] ? v[1].party_name : '',
        party_2_role: v[1] ? v[1].party_role : '',
        party_2_assigned: v[1] ? v[1].state : '',
        party_2_expected: v[1] ? (v[1].expected || '') : '',
        party_3_name: v[2] ? v[2].party_name : '',
        party_3_assigned: v[2] ? v[2].state : '',
        correlative_holds: sv.correlative_holds === true ? 'TRUE' : sv.correlative_holds === false ? 'FALSE' : '',
        time_spent_seconds: sv.time_spent_seconds,
        bond_index: sessionData.bond_index,
      };
    });

    var btn = document.getElementById('de-submit-research');
    if (btn) { btn.disabled = true; btn.textContent = 'Submitting...'; }

    fetch(SHEETS_ENDPOINT, {
      method: 'POST',
      mode: 'no-cors',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rows: rows }),
    }).then(function () {
      if (btn) {
        btn.textContent = 'Submitted \u2713';
        btn.classList.add('de-btn-submitted');
      }
    }).catch(function () {
      if (btn) {
        btn.textContent = 'Submit failed \u2014 try downloading instead';
        btn.disabled = false;
      }
    });
  }

  function downloadJSON(data, filename) {
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function escHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // =========================================================================
  // INIT
  // =========================================================================
  function init() {
    root = document.getElementById('de-game-root');
    if (!root) return;
    render();
  }

  // Export for external init call
  window.initDearEthicistGame = init;
})();

import os
import sys
import json
import re
import unicodedata
from datetime import datetime

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from ai_narrative_segmenter_v2 import (
    segment_messages_into_scenes_v2,
    extract_title_from_text,
    parse_timestamp_v2,
    GM_BOT_ACTORS
)
from unify_characters_v2 import get_canonical_name_v2, build_unified_characters_dict_v2, CHARACTER_METADATA_V2

# Advanced HRP / Excuse / Ping filtering regex
HRP_EXCL_PATTERNS = [
    r'navr[eé].*\b(retard|impr[eé]vu|attente|temps)\b',
    r'd[eé]sol[eé].*\b(retard|impr[eé]vu|attente|temps)\b',
    r'^\s*\|\|.*\|\|\s*$',
    r'^\s*<@&?\d+>\s*$',
    r'^\s*@\S+\s*$',
    r'^\s*@\S+\s+navr[eé]',
    r'^\s*@\S+\s+d[eé]sol[eé]',
    r'^\s*\|\|?\s*<@&?\d+>.*(retard|impr[eé]vu|attente|navr[eé]|d[eé]sol[eé]|question)',
    r'^\s*\(?\s*hrp\s*:.*?\)?\s*$'
]
HRP_EXCL_REGEX = re.compile('|'.join(HRP_EXCL_PATTERNS), re.IGNORECASE)

# 7 Explicit MJ Anchor Messages for 'Grande-salle-porcelaine' (L'Oeil APP / Bot)
MJ_ANCHORS_PORCELAINE = [
    {
        "id": "1509092704389304501",
        "author": "Oeil",
        "timestamp": "2026-05-27T08:00:00Z",
        "content": """Béni soit le fruit.
L'Appel

Un oiseau de mauvais augure, au plumage de jais, se charge de porter un message aux " prétendants " et à leur aîné. Ils sont convoqués, par Sa Sainteté en personne et ils ne peuvent refuser. La Grande Salle de Porcelaine est un endroit agité mais à leur arrivé ; le calme plat, une étrange forme de sérénité.

La curiosité, propre de l'Homme, est dévorante.

Une lumière grise traverse le trou au centre de la salle, baignant celle-ci dans une atmosphère étrange, irréaliste. Le silence de plomb n'est qu'un clou de plus dans le cercueil du doute : L'Oeil, n'est pas une simple guilde.

Sous la lumière d'une pigmentation froide se trouve un individu en capuche, dont le visage n'est pas perceptible même pour ceux se rapprochant. Aucun signe distinctif, d'une taille correct et d'une carrure difficilement estimable par-delà ces vêtements amples. Ce sombre apparat, cette posture droite et imperturbable ainsi que l'absence totale d'agitation s'accordent avec l'idée que les " prétendants " peuvent se faire des protecteurs de la Couronne. Pour l'aîné à la Balafre, c'est une évidence, qu'il s'agit là d'un émissaire, d'un héraut du vecteur de la foi.

Une cloche se met à sonner.

Qu'est-ce qui attend, ceux qui perdront bientôt leurs noms ?"""
    },
    {
        "id": "1509092704389304502",
        "author": "Oeil",
        "timestamp": "2026-05-29T10:25:00Z",
        "content": """Que le Seigneur ouvre.
La Réponse

Tous sont présents, comme souhaité par celui qui accorde la vue. Son héraut relève ce qui cache son visage et bien qu'ils puissent regarder en sa direction, ils sont incapables de le voir. Une ombre, deux yeux, la longueur de ses cheveux, une trace de peau, une peau pâle. Ce pilier de ténèbres fixe chaque membre de cette assemblée simultanément ou, tout du moins, laisse cette désagréable impression d'être épié par le Vide en personne. Un silence de plomb qui fait un bruit cacophonique dans la désolation de leurs esprits, esclaves de la stupeur de l'instant. Conditionnés à être les spectateurs, sa voix s'élève une première fois et résonne comme un doux murmure que l'on porte à l'oreille.

𝐒𝐢𝐥𝐞𝐧𝐜𝐞.

Oculus videt.

Son ombre, omniprésente, s'étend sur le sol comme un être fongique proliférant dans un lieu humide ; elle progresse vite, crée le vide, recouvre les noms et les êtres. Ici, seul l'Oeil s'exprime.

𝐕𝐞𝐧𝐢 𝐔𝐦𝐛𝐫𝐚𝐞𝐥.

La Main noire.

Esotérique, sa voix résonne, faisant trembler le sol, les murs. Sa présence recouvre le tout, s'en imbibe et ne laisse plus rien transparaître. Les prétendants et l'aîné voient leurs jambes tremblées, puis, la chute. Leur corps s'effondre, ne se raccrochant plus à l'Espace et au Temps, comme éloigné de ces concepts futiles. Depuis combien de temps ils chutent ? Une seconde, un mois, peut-être un an. La douleur, quand ils heurtent le sol, est salvatrice.

Trois âme, dans un même lieu qui semble pourtant si différent. Ancien, délabré, ne laissant plus que l'ombre de la vie. Face à eux, l'émissaire du Saint n'est plus. Une brèche immense, trace présumé de son passage ou simple réalité de ce monde aux couleurs ternes

Prométhéen, Pandorienne et Sisyphe.

Un point de singularité qui ne peut être ignoré mais dont la valeur est pour l'instant dévaluée ; au tendre risque de voir leurs Esprits/Âmes/Corps brisées.
Que le Seigneur ouvre.
L'Envers du Monde."""
    },
    {
        "id": "1509092704389304503",
        "author": "Oeil",
        "timestamp": "2026-05-31T14:03:00Z",
        "content": """Par-delà le Voile.
Attentes.

La chute fut douloureuse, pour tous. Des visions, la suffocation et bien d'autres pénitences ont frappé les prétendants et leur aîné. En réponse à l'abîme, le Balafré tente d'animer l'Arcane ; celle-ci lui répond, mais aussitôt apparue, se fit dévoré par les ténèbres insondables de ce lieu, une sensation étrange, presque familière traversant son échine tendue, face à l'urgence de la situation.

En proie à une forme de vérité, ils cèdent.

L'Indigne voit et entend l'Absence et son esprit cherche désespérément à combler ce trou, donnant naissance à un être de rien, produit de son esprit. La Lucide fait face à un parfum familier, qui pourtant la ronge avant de la faire chuter ; membre d'une si illustre famille, comment peut-elle être incapable de dompter ces ténèbres pourtant jusqu'à lors fidèles confidents.

Fissure attrayante, presque rassurante, ils y voient un chemin.

L'air est lourd, les espaces sont creux et le sol est couvert de ce qui semble être de la poussière, ou peut-être des cendres. Mais le silence, compagnon d'infortune se brise, par des bruits de craquement sourds provenant d'une de ces " arches " donnant sur ce qui semble être une infinité de chemins. En levant les yeux, une hauteur désarmante et un ciel gris, mort.

Les bruits s'intensifient, ils résonnent en ces lieux avec une clarté désarmante.

Quelques pas suffissent pour voir ce précipice ; troublant par sa présence comme par cette fraîcheur qu'il dégage. Il fait déjà tellement froid, ou peut-être chaud, à vrai dire ils ne sont pas en mesure de le dire. Dans la vue de la gracié de Pandore, se trouve que des taches, blanches et noires, apparaissant à intervalles irréguliers dans un décor morne. Elle ne le voit pas pourtant, elle ne voit pas le Voile ici.

Des sanglots.

Cassant à nouveau les connaissances et les certitudes ; plus rien ne craque, si ce n'est l'esprit de quelque chose. . . ou de quelqu'un. Les échos brouillent les pistes et s'aventurer trop proche de ce trou béant n'est pas viable ; leurs instincts s'aiguisent.

Finalement, des bruits de pas.
Quelque chose approche.
Par-delà le Voile.
Le Berceau."""
    },
    {
        "id": "1509092704389304504",
        "author": "Oeil",
        "timestamp": "2026-06-05T20:24:00Z",
        "content": """Le Premier couteau.
Mastication irritante

Le bruit constant de ces pas se rapprochant, la roche se brisant et ces étranges craquements. Voilà bien trop longtemps qu'ils sont ici à attendre ; certains cherchent à comprendre, d'autres à survivre, voire à s'offrir à l'Absence. Mais alors que la pièce chute, éternellement, la provenance du son devient identifiable ; sur leur gauche, s'échappant d'une arche lugubre. Le premier invité de ces lieux, à la capuche et aux cheveux blancs ; hétérochrome, ses pupilles fixent la salle, ses lèvres noires, sèches, laissant apparaître un mets qui semble être à sa convenance, la salive s'échappant avec abondance de ses croissants de chair. Ses doigts rugueux se frottent contre la roche, créant un sillon propre dans la saleté de l'architecture. Ses fidèles compagnons, des rats purulents, couinent tandis qu'il laisse toute sa silhouette apparaître à la vue des prétendants et de leur aîné.

Ses dents pointues se referment sur une main humaine, qu'il ingurgite goulûment dans un gloussement joueur.

Sa langue se perd à nouveau contre ses lèvres tandis qu'il fixe avec attention Vesper, qu'il connaît bien, fier d'être sa liaison malsaine avec les directives de l'être sacré. Mais avant qu'il ne puisse ouvrir sa bouche, moqueuse, un croassement se fait entendre, dans l'arche à côté de la sienne. Des plumes noires, porteuses d'un message sinistre, qu'il se permet pourtant d'ignorer, laissant l'odeur pestilentielle de son corps et de son arcane se propager, offrant les " dons " de son Père, à qui le souhaite.

Ils sont en présence de l'Inconnu, l'audace n'a pas lieu d'être
Le Premier couteau.
Le Berceau.
Violence.
Gorge déployé, son rire perce l'air

??? : AH AH AH ! Vesper, le petit balafré devient grand, il visite même le berceau !

Effroyable ironie. Le sang tâche encore le coin de sa bouche, pourtant il n'attend pas pour se saisir d'un œil, qu'il extirpe de sa poche dans un bruit reboutant, portant ce dernier à son visage pour le lécher allègrement devant les prétendants et son " préféré ". Sa pupilles rouge se perd justement sur ces nouveaux arrivants, avant de revenir assez rapidement vers Vesper, puis le sol, disposant d'une attention maigre, inexistante en vérité. Une latence s'instaure avant qu'il ne puisse reprendre la parole, s'adressant toujours et encore au Prométhéen.

??? : Alors, comment c'était de carboniser Gérald ? Il paraît que tu as failli y laisser ta peau. . . Non pas que ça me dérange, au contraire mais euh-... Ah oui pardon je dois pas dire ça. Je suis un peu tête en l'air quand j'ai faim, je suis navré.

Il ne bouge pas, fixer au sol, sa place légitime.

Observant depuis sa hauteur les membres de l'Oeil, cet agent chaotique est une énigme aussi intéressante qu'absurde que rares s'amusent à décrypter ; pour cause, son régime alimentaire rigide, qui contraint souvent à des échanges peu valorisants, pour l'espèce Humaine.

??? : M'enfin c'est pas très important, ce qui compte c'est que tu sois là. Papa risque de ne pas trop tarder, si nos autres frères se décident à sortir le bout de leurs nez. Au fait je crois que j'ai déchiqueter Nox, tu m'en veux pas hein ? Tu sais j'ai entendu dire qu - ...

Son flot constant de paroles provoque une irritation palpable et son manque de rigueur ne déclenche rien de plus qu'une correction approprié. Les oiseaux de mauvaise augure se déchaînent subitement, s'échappant de l'Arche en apportant une nouvelle présence en ces lieux. Un visage froid, un calme presque perturbant dans le chaos ambient. Des pupilles de jais, et une longue cape noire couvrant son corps

Un masque de craie, tout aussi effrayant que le héraut de la pourriture.
Violence.
Le choix délibéré d’atteindre la fin par n’importe quel moyen.
Hypocrisie.
Il commence par son nom.

??? : Silence, Abaddon.

Un vent frais, presque salvateur du fétide et de sa peste qui gangrène l'air.

En guise de seule réponse, l'anthropophage marque le silence, comme un animal obéissant à son maître, n’oubliant pas de jeter un regard noir, crachant de la rancœur envers celui qui le coupe de son macabre amusement. Sa posture est droite, presque parfaite, trahissant rigueur et discipline. Cet apôtre du changement, vassal d'un maître qu'ils ne connaissent pas encore, se montre sous un jour attrayant ; bien loin de l'idée de confiance, il est pourtant celui qui s'aligne le plus avec les traits de l'Homme, dans sa nature première. Mais une fois de plus, les apparences sont sûrement trompeuses. L'Oeil n'est que le réceptacle d'une mission sacrée : Protéger la Couronne. La Ferveur balaye tout autre sentiment.

Baël : Baël.

Nom.

C'est ce qu'ils peuvent voir et entendre. Un nom, sûrement le sien, aussi ésotérique et troublant que celui du Porte-Peste. Fixe, ses pieds ne quittent pas sa place, celle dont il est légitime. L'air se mit soudainement à vibrer, attirant les regards : Un autre agent se présente, précepte nouveau d'un livre sacré dont ils connaissent à peine l'intitulé. C'est à l'opposé du " Parfait " qu'ils peuvent observer l'intangible et l'irrationnel ; une orbe à la forme changeante, perturbant la vue, l'ouïe, le toucher et le goût par sa simple présence. Celle-ci s'insinue dans les esprits avec légèreté, rappelant l'exploit du Sans-visage ayant accueilli la troupe.

Peut-on seulement parler de " l'Homme " lorsqu'on le désigne ?
Hypocrisie.
Elle n'est que l'hommage que la vérité paie à l'erreur.
Perfidie.
Volatile, sa trace est un doute et une certitude.

Dans un silence de plomb il est ce bourdonnement qui rappel sa condition mortelle. Une piqûre vive dans la peau qui frétille sous son joug. Il ne touche absolument rien et pourtant il semble être au contact de tout ; se glissant sous la peau des vivants, comme un insecte frétillant, lubrique, cherchant à se satisfaire de ce qu'on lui offre. De loin le plus rebutant, aux côtés du Pestilentiel, cet astre mort semble totalement incapable de communiquer par les mots ; il n'est que sensations, que vibrations. Un contact aussi dégradant qu'un canidé s'imprégnant des odeurs de l'un de ses confrères. Mais l'effroi ne se stoppe pas aux mœurs de l'Horreur, elle se développe bien au-delà.

• ｡ ◦ ∙ ▪▲─◊◊◊

*

.тɘbiv ƨυlυɔo .ɘяяɘv υb тɘ ƨɘяɘ̀iмυl ƨɘb ɘяɘ̀iяяɘb ɘнɔɒɔ ɘт υт ɘυp тiɒƨ ,тîɒииoɔ ɘт ɘllɘ

L'Esprit est incapable de traduire ce que l'Âme ne veut pas comprendre, faisant vibrer le corps au rythme milimètré de l'Horloge, divinité sinistre, patron de la Non-vie. Mais le parfum ignoble de l'incompréhension est balayé par l'exquis, celui qui provoque, qui attire, séduit, dans une infinités de promesse réjouissantes allant de la chair, en passant par l'Or puis le trône. Dans l'arche opposant le fétide, s'extirpe une figure enivrante, porteur d'un message bien moins complexe, celui d'ouvrir les portes de son être à sa nature. Pourtant, sa subtilité est sans égale, tandis que l'air murmure son nom.

Däsmodée
Perfidie.
Immonde, elle se cache derrière l'innocence.
Excès.
Sa senteur embrume l'espace, détachant les âmes du tourment qu'offre le Trompeur.

Däsmodée : En voilà une assemblée... Singulière. Ce n'est cependant pas déplaisant de voir les nouveaux suivants de Sa Sainteté, ou même le tristement célèbre Vesper. Qu'est-ce que tu me rappelles Loyis. . .

Les yeux plissés, il secoue légèrement le menton et s'extirpe de l'ombre.

Une odeur de fleur, dans un espace n'en contenant pas. Ses pupilles rubis s'accrochent aux Sans-noms, particulièrement à celle qui s'accorde généralement avec les morts. L'héritière noble ressent alors, une chaleur nouvelle, celle du besoin et de l'envie, comme dans l'attrait soudain, l'appel dérangeant de la chair. Cet homme est beau, très beau, trop beau. Son regard est pesant, comme une poigne que l'on désire plus que tout rompre. Et lorsqu'il daigne enfin lâcher la Pandorienne du regard, c'est une véritable libération. Celui-ci ne perd pas de temps et montre son impatience.

Däsmodée : Je vois que le maître de Cérémonie est pour le moment absent. C'est n'est pas le travail qui manque, mes frères ;l'objet de cette assemblée vaut-elle vraiment notre présence à tous ?

Il n'obtenu aucune réponse.

Un soupir, maladroit, montrant son agacement. Sa tenue, digne d'un noble de haute lignée trahit assez grossièrement son rang, son titre. La confiance qu'il dégage est contagieuse ; elle couvre les yeux et ouvre dans les esprits, la porte silencieuse, celle qu'on a muselée sous le bon sens. Il est le dernier à se présenter et offre enfin une bouffée d'air, brève, aux prétendants et à leur aîné. Qu'est-ce qu'ils attendent ? Pourquoi ce gouffre semble soudainement si attirant ? L'odeur est nauséabonde non ? Ce bourdonnement est insupportable. Pourquoi est-ce Baël à un grain de beauté ?

La Tempête sous le crâne est le supplice qu'on réserve à l'ignorance. Sont-ils ignorants ? Peut-être. Sûrement.
Excès.
Elle peut tout gâter, même la sagesse."""
    },
    {
        "id": "1509092704389304505",
        "author": "Oeil",
        "timestamp": "2026-06-11T11:29:00Z",
        "content": """Le Berceau.
Le Miroir.

La Pourriture ricane face à la naïveté du fils Enjaku mais ne s'exprime pas et se contente de regarder l'arche centrale.

Ses frères ne tardent pas à en faire de même, annonçant l'arrivée prochaine de celui qu'ils attendent. Une démarche lente, sonore : L'écho de ses bottes contre la roche sale et cendreuse s'intensifie au fur et à mesure que le temps passe. Certains se laissent dépasser par l'incertitude, d'autres y voient là une liberté totale et absolue et le mouton noir ne fait qu'attendre, résolut, comme un enfant insatisfait de sa situation.

Ironique.

L'air est lourd, et si chacune des arche qu'ils explorent laisse une trace unique, celle-ci est différente. Il ne se dégage pas d'effroi, de terreur ni d'incertitude lorsqu'il s'approche enfin d'une lumière rendant son visage perceptible, lui, maître des ombres insondables.

Quelque chose ou plutôt quelqu'un de simple se présente à eux.
.
Le Berceau.
Le Miroir.
Un Homme, grand, brun, comme il y en a des milliers à Espéria.

Son regard est de fer, l'absence de sourire assure sa discipline, chose que l'aîné des prétendants ne peut que comprendre. Pour l'enfant de Vaelric, ces yeux sont étonnamment familiers ; cette rigidité ne cache rien d'autre qu'une Vision, si claire, qu'elle peut même transparaître sur ses pupilles. Ses lèvres ne se sont toujours pas quittées et pourtant, on lui accorde le silence, comme un droit divin, dans l'obéissance totale et absolue qui lui est naturellement dû.

Un tâche. Non, plusieurs.

Seule témoin de cette facette du monde, l'Enfant des morts n'est que spectatrice de tâches, pourtant signes de sa famille, sur le visage mais aussi sur le corps du nouvel arrivant. Une illusion ? Un message ? Un présage ? Rien ne vaut la Foi aveugle face à l'absence, que la Déesse la protège, pauvre Pandorienne.

— N'est-ce pas avisé de s'assurer du tranchant de sa lame avant de partir en guerre ?

Son menton dévie et aligne son visage avec celui du Balafré.

Le silence est la seule réponse adéquate ici.

— Sous son oeil.

Une Prière qui rend l'air un peu plus respirable, répété avec exactitude par l'ensemble des quatre doigts formant cette main étrange de l'autorité.

Cet homme semble, en tout point et à première vue, d'une banalité affligeante. Il ne porte pas les apparats des nobles mais n'est pas couvert par la disgrâce des gueux et autre prolétaire. Il ressemble en tout point à homme que l'on croise au marché ou au port ; rien ne le démarque si ce n'est l'infini respect qu'on semble lui porter. Il est un miroir, étouffant, car l'on y voit que son reflet. Son attention se fige alors sur le survivant de la Purge, héritier désormais illégitime des Vaelric-Farlier.

— Tu viens de naître, par sa main. Tu n'es plus rien et il te reste à définir ce que tu es, Iscarioth.

Dans le creux de sa paume.

Dis-moi, qu'est-ce que tu es ?

La Première Ascencion.

La fraternité vient d'un rôle commun ; qu'est-ce que sont les membres de l'Oeil ?
Le Miroir."""
    },
    {
        "id": "1509092704389304506",
        "author": "Oeil",
        "timestamp": "2026-06-23T19:03:00Z",
        "content": """L'Orfèvre.
Sous son oeil.

Un frère vient de naître par sa main et son porteur de vérité n'affiche ni satisfaction, ni plaisir. D'une effroyable neutralité, il se contente de faire ce qu'il doit faire, portant les marques de son rôle, la tenue de Père, l'effroi de sa Mère. Lui est, à la fois certitudes et contradictions, dans le climat animal de la guerre silencieuse dont il maîtrise les pièces et ici, il obtient un nouveau fou. Sa collection s'étoffe car, pour la Couronne, aucun prix n'est trop grand.

Bien.

Son regard dévie vers la fille de la Mort.

Tenebris. Que l'air gagne tes poumons et t'offre la joie de vivre par sa main.

Un prisme de sa mortalité.

Lorsque l'on passe une vie entière à côtoyé la mort, la beauté de la vie s'estompe parfois. Pourtant, ici, elle ne peut rester insensible à cet air qu'elle aspire, qu'elle consomme, qu'elle consume. Porteuse de son nouveau nom, la fille Dandelion n'est plus ; il ne reste plus qu'elle, celle qui porte le voile des ténèbres. Mais reste cette interrogations vitale, celle de connaître son rôle.

Ouvre la bouche et parle. Qu'est-ce que tu es ?

Un outil à son service.

L'incarnation de sa volonté
L'Orfèvre."""
    },
    {
        "id": "1509092704389304507",
        "author": "Oeil",
        "timestamp": "2026-07-03T23:00:00Z",
        "content": """Par sa voix.
Un songe.

Là encore, l'absence de réaction n'est qu'une confirmation silencieuse de son absolue sagesse, sa plénitude sur le mondes des Hommes. Si les prétendants se sont montrés dignes, ils se doivent de recevoir le serment sous sa forme la plus pure, la plus physique. Un bruit métallique se fait entendre, comme une objet mouvant, rapide, fendant l'air. Le Gouffre laisse apparaître une lumière ; ce qui est particulièrement surprenant, pour le dévoreur . Cette pièce est celle de l'Orfèvre, qui remonte le vide par la seule volonté de celui qui voit. Celle-ci va rejoindre sa dextre est être brisé, compressé dans sa poigne dans un bruit strident, perturbant, envoûtant. Puis il lâche et délivre, dans l'espace, deux médaillons teinté par une lueur noir, symbole d'appartenance aux suivants de Sa Sainteté.

L'Erreur n'est pas toléré, l'échec n'est pas envisagé.

Le Contrat.

Vous prendrez sa marque et exécuterez sa volonté.

Les Médaillons flottent jusqu'à atteindre les prétendants, désormais nouveaux membres de la Confrérie.

Trouvez Vox, la voix. Il est temps de le rendre à Ifrit.

Faire preuve de compassion.

Une fois entre les mains de leurs propriétaires légitimes, les yeux du Saint s'éveillent. Il observe, silencieusement ses nouveaux enfant et son regard, d'une bienveillance froide, religieuse. Sa presence est tout de même notable tant le simple fait de voir, est une bénédiction, maintenant qu'ils font partie de lui. Leur aîné, Sa Voix , leur accorde une dernière mélodie.

Par ses yeux, vous pourrez rejoindre notre Berceau, 𝐔𝐦𝐛𝐫𝐚𝐞𝐥, mais aussi le monde d'au-dessus, l'entre-murs de la cité d'or. Les " Voies " sont les passages bénis par sa grâce, nous permettant d'être partout et nul part à la fois.

Leurs aînés, pour illustrer les propos de Celui qui sait, s'éloignent dans ses longs couloirs laissant leurs pas s'évanouir dans l'Absence. Les consignes cryptiques deviennent des cantiques d'une absolue clarté, comme une évidence désormais pour l'Orfèvre et le Songe. Leur rôle est maintenant d'honorer le serment : l'échec n'est pas tolérable.

Mais sans savoir qui ils poursuivent, comment faire ?
Par sa voix.
Obscurantisme & Omnipotence."""
    }
]

def clean_channel_name(channel_raw):
    if not channel_raw:
        return "Salon RP"
    
    norm = unicodedata.normalize('NFKC', channel_raw)
    clean = re.sub(r'[^\w\s\-\'’àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', '', norm).strip()
    clean = re.sub(r'\s+', ' ', clean)
    return clean if clean else channel_raw.strip()

def format_canonical_iso_time(ts_str):
    ts_val = parse_timestamp_v2(ts_str)
    if ts_val > 0:
        dt = datetime.fromtimestamp(ts_val)
        return dt.isoformat() + "Z"
    return str(ts_str)

def get_message_full_text(m):
    content = str(m.get('content', '') or '').strip()
    embed_title = str(m.get('embed_title', '') or '').strip()
    embed_desc = str(m.get('embed_description', '') or '').strip()

    parts = [p for p in [embed_title, embed_desc, content] if p]
    
    unique_parts = []
    for p in parts:
        if p not in unique_parts:
            unique_parts.append(p)

    full = '\n\n'.join(unique_parts).strip()
    return full

def is_meaningful_rp_content_v2(content):
    if not content:
        return False
    
    text = str(content).strip()
    if not text:
        return False

    if text.startswith('||') and text.endswith('||'):
        return False

    if HRP_EXCL_REGEX.search(text):
        return False

    clean = re.sub(r'<@[!&]?\d+>', '', text)
    clean = re.sub(r'<#\d+>', '', clean)
    clean = re.sub(r'\[Image:\s*https?://\S+\]', '', clean)
    clean = re.sub(r'https?://\S+', '', clean)
    clean = re.sub(r'\[.*?\]\(https?://\S+\)', '', clean)
    clean = re.sub(r'@[^\n@]+', '', clean)
    
    letters_only = re.sub(r'[^\w]', '', clean, flags=re.UNICODE).replace('_', '').strip()

    if len(letters_only) < 5:
        lower = letters_only.lower()
        if lower in ['ping', 'up', 'relance', 'atoai', 'atois', 'avous', 'hrp', 'inrp', 'ok', 'thx', 'oeil', 'loeil']:
            return False

    return len(letters_only) >= 3

def compute_faction_distribution(actors, characters_dict):
    factions = {}
    for act in actors:
        char_info = characters_dict.get(act, CHARACTER_METADATA_V2.get(act, {}))
        role = char_info.get('role', 'Indéfini') if isinstance(char_info, dict) else 'Indéfini'
        factions[role] = factions.get(role, 0) + 1
    return factions

def compute_location_image(channel_clean):
    img_dir = "public/channel_images"
    if not os.path.exists(img_dir):
        return None

    img_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    
    ch_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFD', channel_clean.lower())).strip()
    for img in img_files:
        base = os.path.splitext(img)[0]
        base_c = re.sub(r'[^\w]', '', unicodedata.normalize('NFD', base.lower())).strip()
        if base_c and (base_c == ch_c or base_c in ch_c or ch_c in base_c):
            return f"channel_images/{img}"

    fallback_map = {
        'cellules': 'channel_images/cellules.jpg',
        'serredelune': 'channel_images/serre-de-lune.jpg',
        'fontainemarbree': 'channel_images/fontaine-marbree.jpg',
        'terrassecouverte': 'channel_images/terrasse-couverte.jpg',
        'parcdescardinaux': 'channel_images/parc-des-cardinaux.jpg',
        'cantinemarbree': 'channel_images/cantine-marbree.jpg',
        'jardindequartz': 'channel_images/jardin-de-quartz.jpg',
        'vergerdespeches': 'channel_images/verger-des-peches.jpg',
        'leberceau': 'channel_images/le-berceau.jpg',
        'coursfleurie': 'channel_images/cours-fleurie.jpg'
    }
    
    for key, val in fallback_map.items():
        if key in ch_c or ch_c in key:
            return val

    return None

def create_scene_object_v2(channel_clean, channel_raw, scene_index, message_tuples, title_suggested):
    rp_msgs = [m for m in message_tuples if is_meaningful_rp_content_v2(m[1])]
    if not rp_msgs:
        rp_msgs = message_tuples

    first_msg = rp_msgs[0][0]
    last_msg = rp_msgs[-1][0]

    raw_actors = set()
    total_words = 0

    for msg, text in rp_msgs:
        author = msg.get('author_name', msg.get('author', ''))
        canon = get_canonical_name_v2(author)
        raw_actors.add(canon)
        total_words += len(text.split())

    actors = list(raw_actors) if raw_actors else ["Narrateur"]
    main_actor = actors[0] if actors else "Narrateur"

    start_iso = format_canonical_iso_time(first_msg.get('timestamp', ''))
    end_iso = format_canonical_iso_time(last_msg.get('timestamp', ''))

    start_ts = parse_timestamp_v2(first_msg.get('timestamp'))
    end_ts = parse_timestamp_v2(last_msg.get('timestamp'))
    duration_mins = max(1, int((end_ts - start_ts) / 60)) if (end_ts > start_ts and start_ts > 0) else 1

    preview = rp_msgs[0][1]
    clean_p = re.sub(r'^\s*\|\|?\s*<@&?\d+>\s*\|\|?', '', preview).strip()
    if clean_p:
        preview = clean_p

    if len(preview) > 160:
        preview = preview[:157] + "..."

    location_image = compute_location_image(channel_clean)
    scene_id = f"scene_{re.sub(r'[^a-zA-Z0-9]', '_', channel_clean).lower()}_{scene_index}"

    return {
        "id": scene_id,
        "channel": channel_raw,
        "channel_raw": channel_raw,
        "channel_clean": channel_clean,
        "title": title_suggested if title_suggested else f"{channel_clean} — Scène {scene_index}",
        "actors": actors,
        "main_actor": main_actor,
        "start_time": start_iso,
        "end_time": end_iso,
        "duration_minutes": duration_mins,
        "preview": preview,
        "message_count": len(rp_msgs),
        "word_count": total_words,
        "location_image": location_image,
        "messages": [
            {
                "id": m[0].get('id', ''),
                "author": get_canonical_name_v2(m[0].get('author_name', m[0].get('author', ''))),
                "timestamp": format_canonical_iso_time(m[0].get('timestamp', '')),
                "content": m[1]
            }
            for m in rp_msgs
        ]
    }

def main():
    print("=== Démarrage du re-tri V2 avec Prise en charge intégrale de TOUS les Bots RP / Tupperbots ===")

    src_file = 'src/scenes.json' if os.path.exists('src/scenes.json') else 'scenes.json'
    if not os.path.exists(src_file):
        print(f"Erreur : Impossible de trouver '{src_file}'")
        return

    with open(src_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    existing_scenes = raw_data.get('scenes', raw_data if isinstance(raw_data, list) else [])

    channels_map = {}
    for sc in existing_scenes:
        ch_raw = sc.get('channel_raw', sc.get('channel', 'Salon Inconnu'))
        ch_clean = clean_channel_name(ch_raw)

        if ch_clean not in channels_map:
            channels_map[ch_clean] = {'raw': ch_raw, 'messages': []}

        msgs = sc.get('messages', [])
        if msgs:
            for m in msgs:
                full_text = get_message_full_text(m)
                if is_meaningful_rp_content_v2(full_text):
                    if m.get('id') in ['1509092704389304502', '1509092704389304503'] and 'Que le Seigneur' not in full_text and 'La Réponse' not in full_text and 'Attentes' not in full_text:
                        continue
                    if 'Béni soit le fruit' in full_text or m.get('id') == '1509092704389304501':
                        m['author'] = 'Oeil'
                        m['author_name'] = 'Oeil'
                    channels_map[ch_clean]['messages'].append((m, full_text))

    # Anchor ALL 7 MJ Messages into 'Grande-salle-porcelaine' with exact timestamps
    if 'Grande-salle-porcelaine' in channels_map:
        anchor_dict = {anc['id']: anc for anc in MJ_ANCHORS_PORCELAINE}
        updated_msgs = []
        for m, txt in channels_map['Grande-salle-porcelaine']['messages']:
            m_id = m.get('id')
            if m_id in anchor_dict:
                anc = anchor_dict[m_id]
                m['timestamp'] = anc['timestamp']
                m['author'] = 'Oeil'
                m['author_name'] = 'Oeil'
                m['content'] = anc['content']
                updated_msgs.append((m, anc['content']))
            else:
                updated_msgs.append((m, txt))
        channels_map['Grande-salle-porcelaine']['messages'] = updated_msgs

        for anchor_item in MJ_ANCHORS_PORCELAINE:
            anc_id = anchor_item['id']
            anc_content = anchor_item['content']
            snippet_check = anc_content[:40].strip()
            
            already_present = any(
                m[0].get('id') == anc_id or (m[0].get('author') == 'Oeil' and snippet_check in m[1])
                for m in channels_map['Grande-salle-porcelaine']['messages']
            )
            if not already_present:
                channels_map['Grande-salle-porcelaine']['messages'].append((anchor_item, anc_content))

    all_v2_scenes = []

    for ch_clean, ch_info in channels_map.items():
        ch_raw = ch_info['raw']
        sorted_msgs = sorted(ch_info['messages'], key=lambda x: parse_timestamp_v2(x[0].get('timestamp', '')))
        valid_msgs = [m for m in sorted_msgs if m[1].strip()]

        if not valid_msgs:
            continue

        ch_scenes = segment_messages_into_scenes_v2(
            ch_clean,
            ch_raw,
            valid_msgs,
            create_scene_object_v2
        )
        all_v2_scenes.extend(ch_scenes)

    all_v2_scenes.sort(key=lambda s: parse_timestamp_v2(s.get('start_time', '')))

    # Post-processing — Passe 1 : fusionner les en-têtes isolées (1 msg) dans la scène suivante du même canal (< 24h)
    pass1 = []
    idx = 0
    while idx < len(all_v2_scenes):
        sc = all_v2_scenes[idx]
        if (
            sc.get('message_count', 0) == 1
            and idx + 1 < len(all_v2_scenes)
            and all_v2_scenes[idx + 1].get('channel_clean') == sc.get('channel_clean')
        ):
            next_sc = all_v2_scenes[idx + 1]
            gap = parse_timestamp_v2(next_sc.get('start_time')) - parse_timestamp_v2(sc.get('end_time'))
            if gap <= 24 * 3600:
                next_sc['messages'] = sc['messages'] + next_sc['messages']
                next_sc['start_time'] = sc['start_time']
                next_sc['actors'] = list(set(sc['actors'] + next_sc['actors']))
                next_sc['message_count'] = len(next_sc['messages'])
                idx += 1
                continue
        pass1.append(sc)
        idx += 1

    # Post-processing — Passe 2 : fusionner les conclusions isolées (1 msg) dans la scène précédente du même canal
    pass2 = []
    for sc in pass1:
        if sc.get('message_count', 0) == 1:
            # Chercher la scène précédente dans le même canal (pas forcément la dernière dans pass2)
            prev_same = None
            for prev in reversed(pass2):
                if prev.get('channel_clean') == sc.get('channel_clean'):
                    prev_same = prev
                    break
            if prev_same is not None:
                prev_same['messages'] = prev_same['messages'] + sc['messages']
                prev_same['end_time'] = sc['end_time']
                prev_same['actors'] = list(set(prev_same['actors'] + sc['actors']))
                prev_same['message_count'] = len(prev_same['messages'])
                continue
        pass2.append(sc)

    all_v2_scenes = pass2
    characters_v2 = build_unified_characters_dict_v2(all_v2_scenes)

    for sc in all_v2_scenes:
        sc['faction_distribution'] = compute_faction_distribution(sc.get('actors', []), characters_v2)

    output_v2_data = {
        "metadata": {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "total_scenes": len(all_v2_scenes),
            "total_characters": len(characters_v2)
        },
        "characters": characters_v2,
        "scenes": all_v2_scenes
    }

    all_target_json_paths = [
        'src/scenes_v2.json',
        'scenes_v2.json',
        'src/scenes.json',
        'scenes.json'
    ]

    for p in all_target_json_paths:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(output_v2_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Fichier mis à jour avec tous les Tupperbots RP : {p}")

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write('window.rpData = ')
        json.dump(output_v2_data, f, indent=2, ensure_ascii=False)
        f.write(';\n')
    print("💾 Fichier data.js synchronisé !")

    print(f"\n✨ Re-tri V2 avec Intégration Totale des Bots RP terminé ! Total : {len(all_v2_scenes)} scènes et {len(characters_v2)} personnages.")

if __name__ == '__main__':
    main()

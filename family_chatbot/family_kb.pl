% Family knowledge base — facts and derived relationship rules

% --- Facts ---

% parent(Parent, Child)
parent(haseeb, ahmed).
parent(haider, ali).
parent(haider, sara).
parent(nadia, ali).
parent(nadia, sara).
parent(ali, laiba).
parent(ali, usman).
parent(zara, laiba).
parent(zara, usman).
parent(kamran, haider).
parent(rukhsana, haider).
parent(kamran, hina).
parent(rukhsana, hina).

% male(Person)
male(haseeb).
male(ahmed).
male(haider).
male(ali).
male(usman).
male(kamran).

% female(Person)
female(nadia).
female(sara).
female(laiba).
female(zara).
female(rukhsana).
female(hina).

% married(Husband, Wife)
married(haider, nadia).
married(ali, zara).
married(kamran, rukhsana).

% age(Person, Years)
age(kamran, 75).
age(rukhsana, 70).
age(haider, 50).
age(nadia, 48).
age(hina, 45).
age(ali, 28).
age(zara, 26).
age(sara, 24).
age(laiba, 5).
age(usman, 3).

% --- Rules (31) ---

father(X, Y)              :- parent(X, Y), male(X).
mother(X, Y)              :- parent(X, Y), female(X).
grandfather(X, Y)         :- father(X, Z), parent(Z, Y).
grandmother(X, Y)         :- mother(X, Z), parent(Z, Y).
grandparent(X, Y)         :- parent(X, Z), parent(Z, Y).
sibling(X, Y)             :- parent(Z, X), parent(Z, Y), X \= Y.
brother(X, Y)             :- sibling(X, Y), male(X).
sister(X, Y)              :- sibling(X, Y), female(X).
son(X, Y)                 :- parent(Y, X), male(X).
daughter(X, Y)            :- parent(Y, X), female(X).
uncle(X, Y)               :- brother(X, Z), parent(Z, Y).
aunt(X, Y)                :- sister(X, Z), parent(Z, Y).
cousin(X, Y)              :- parent(A, X), parent(B, Y), sibling(A, B).
nephew(X, Y)              :- sibling(Y, Z), son(X, Z).
niece(X, Y)               :- sibling(Y, Z), daughter(X, Z).
ancestor(X, Y)            :- parent(X, Y).
ancestor(X, Y)            :- parent(X, Z), ancestor(Z, Y).
descendant(X, Y)          :- ancestor(Y, X).
husband(X, Y)             :- married(X, Y).
wife(X, Y)                :- married(Y, X).
spouse(X, Y)              :- married(X, Y).
spouse(X, Y)              :- married(Y, X).
father_in_law(X, Y)       :- spouse(Y, Z), father(X, Z).
mother_in_law(X, Y)       :- spouse(Y, Z), mother(X, Z).
brother_in_law(X, Y)      :- spouse(Y, Z), brother(X, Z).
sister_in_law(X, Y)       :- spouse(Y, Z), sister(X, Z).
is_elder(X, Y)            :- age(X, AX), age(Y, AY), AX > AY.
is_younger(X, Y)          :- age(X, AX), age(Y, AY), AX < AY.
elder_sibling(X, Y)       :- sibling(X, Y), is_elder(X, Y).
younger_sibling(X, Y)     :- sibling(X, Y), is_younger(X, Y).
paternal_grandfather(X, Y) :- father(Z, Y), father(X, Z).

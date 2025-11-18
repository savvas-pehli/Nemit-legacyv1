def greek_to_latin(text: str) -> str:
    greek_alphabet = 'ΑαάΒβΓγΔδΕεέΖζΗηήΙιίΚκΛλΜμΝνΟοόΠπΡρΣσςΤτύυΦφΩωώ'
    latin_alphabet = 'AaaVvGgDdEeeZzIiiIiiKkLlMmNnOooPpRrSssTtuuFfOoo'
    table = str.maketrans(greek_alphabet, latin_alphabet)
    translit = text.translate(table)
    translit = translit.translate({ord('Θ'):'Th',ord('θ'):'th',ord('Ψ'):'Ps',
                                   ord('ψ'):'ps',ord('Χ'):'Ch',ord('χ'):'ch',
                                   ord('Υ'):'Hy'})
    return translit
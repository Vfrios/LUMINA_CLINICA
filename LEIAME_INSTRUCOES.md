# LÚMINA — Instruções para abrir o projeto no Sweet Home 3D

## Conteúdo
```
LUMINA_CLINICA/
├── projeto/LUMINA_Clinica.sh3d      ← projeto completo (paredes, ambientes, portas, janelas, móveis, luzes)
├── modelos/                         ← todos os modelos 3D em OBJ + MTL (1 pasta por peça, com ícone .png)
│   ├── recepcao/  maca/  ultraformer/  lavieen/  armarios/  decoracao/
│   ├── portas/  banheiros/  copa/  dml/  deposito/  equipamentos/  espera/  funcionarios/
│   ├── iluminacao/  salas/  tecnica/  consultorio/
│   └── predio_completo/LUMINA_Clinica_completa.obj   ← prédio inteiro em 1 peça (plano B)
├── texturas/                        ← porcelanato areia/claro, mármore, madeira ripada, marsala, terracota
├── planta/planta_2D.pdf, planta_2D.png
├── renders/                         ← 9 imagens conceituais (vista aérea, superior, recepção, espera, Consultório 1, Consultório 2, corredor e banheiros)
├── codigo_fonte/                    ← scripts Python que geram tudo (ajuste e rode de novo se quiser mudar o layout)
├── LISTA_AMBIENTES.md   verificacao.txt   LEIAME_INSTRUCOES.md
```

## Caminho A (preferencial): abrir o .sh3d
1. Instale o Sweet Home 3D (versão 6.x ou superior recomendada).
2. Menu **Arquivo > Abrir…** e escolha `projeto/LUMINA_Clinica.sh3d`.
3. Use **Vista 3D > Vista aérea** (ou "Modificar vista 3D") e o **modo visitante virtual** para percorrer a clínica.

**Aviso honesto:** o arquivo foi montado programaticamente (formato Home.xml dentro do .sh3d) e **não pôde ser aberto no Sweet Home 3D real** durante a criação, pois o programa não estava disponível no ambiente. A estrutura foi validada (XML bem formado, todas as referências internas existem), mas o carregamento real precisa ser confirmado por você. Se o programa recusar o arquivo, use o Caminho B.

Também vale conferir depois de abrir: (a) o sentido de abertura das portas na planta (arcos) — se algum vier invertido, selecione a porta e use Modificar > espelhar; (b) o brilho das luzes; (c) as cores/texturas dos pisos.

## Caminho B (plano de contingência): importar os modelos
1. Abra o Sweet Home 3D com um projeto novo.
2. **Mobiliário > Importar mobiliário…** e escolha o `.obj` desejado (por exemplo `modelos/predio_completo/LUMINA_Clinica_completa.obj`). Na janela, marque a orientação "frente" para o lado que dá para você; as dimensões já são reais (cm).
3. Com o prédio completo importado como uma peça (1000 × 1390 × 300 cm), posicione em x=500, y=1305. Para montar você mesmo, importe as peças de `modelos/*` individualmente e use `planta/planta_2D.png` como **imagem de fundo** (Planta > Importar imagem de fundo, escala: 10,00 m de largura).
4. Texturas: **Modificar cômodo > Textura do piso > Importar** com os PNG de `texturas/`.

## Observações sobre os modelos
- Os modelos Ultraformer e Lavieen são **representações volumétricas ilustrativas** (console com tela, braço e peça de mão), em tamanho compatível com equipamentos reais; não são réplicas oficiais das marcas.
- Os renders (`renders/`) foram gerados por um rasterizador simples próprio: são conceituais, sem sombras/reflexos. Para imagens fotorrealistas use **Foto > Criar foto** dentro do Sweet Home 3D.

## Aviso importante
Projeto **CONCEITUAL**. Não afirma conformidade com normas sanitárias (ex.: RDC 50/ANVISA), acessibilidade (NBR 9050), instalações elétricas/hidráulicas, prevenção de incêndio ou legislação local. Essas verificações devem ser feitas por profissional habilitado.

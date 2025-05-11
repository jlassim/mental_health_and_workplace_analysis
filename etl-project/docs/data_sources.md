
###  docs/data_sources.md

```markdown
# Documentation des Sources de Données

## 1. Données OECD (2024)

### Métadonnées
- **Source** : [OECD Statistics](https://stats.oecd.org/)
- **Période** : 2020-2024
- **Format** : CSV (15MB)
- **Licence** : OECD Terms of Use

### Schéma Original
| Colonne | Type | Description |
|---------|------|-------------|
| LOCATION | str | Code pays (ISO3) |
| INDICATOR | str | Code indicateur |
| OBS_VALUE | float | Valeur numérique |
| UNIT_MEASURE | str | Unité de mesure |

### Indicateurs Clés
- `CG_SENG` : Égalité des genres en STEM
- `HS_LEB` : Espérance de vie
- `JE_LTUR` : Taux de chômage long terme

## 2. Enquête Santé Mentale (2014)

### Métadonnées
- **Source** : [OSMI Mental Health Survey](https://osmihelp.org)
- **Échantillon** : 1,250 répondants
- **Pays** : 15 pays majoritairement occidentaux
- **Variables Sensibles** : Genre, Santé mentale

### Colonnes Importantes
| Colonne | Type | Description | Traitement |
|---------|------|-------------|------------|
| age | int | Âge du répondant | [18-100] |
| gender | str | Genre | Standardisé |
| work_interfere | str | Impact sur travail | Mapping numérique |

## 3. Enquête Santé Mentale (2016)

### Améliorations vs 2014
- Ajout de questions sur les avantages sociaux
- Meilleure couverture géographique
- Variables supplémentaires sur l'entreprise

### Problèmes Connus
- 30% de valeurs manquantes sur `mental_health_benefits`
- Incohérences dans les tailles d'entreprise

## Mapping des Pays

```python
country_mapping = {
    'United States': 'USA',
    'US': 'USA',
    'United Kingdom': 'UK',
    'Deutschland': 'DE' 
}
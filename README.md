# hyperv-ansible

Blueprint Ansible pour **gérer un environnement Hyper-V + SCVMM en multisite**.

Cette version couvre :
- une base d'exploitation utile pour la **Live Migration** (Hyper-V + SCVMM) ;
- une couche **SCVMM hors Live Migration** pour créer/maintenir des objets coeur (host groups, library shares, logical networks, VM networks, clouds) ;
- des contrôles d'entrée (validation de variables) et un mode simulation côté SCVMM.

---

## Objectif

Permettre une configuration standardisée par défaut, puis des surcharges par site/cluster:
- tronc commun global (authentification, performance SMB/Compression, etc.) ;
- overrides par cluster (nombre de migrations simultanées, sous-réseaux autorisés, etc.) ;
- garde-fous pour éviter des dérives d'affectation SCVMM (host group attendu).

---

## Arborescence

```text
.
├── inventories/
│   └── multisite/
│       ├── hosts.yml
│       └── group_vars/
│           └── all.yml
├── playbooks/
│   └── configure_livemigration.yml
└── roles/
    ├── hyperv_livemigration/
    │   ├── defaults/
    │   │   └── main.yml
    │   └── tasks/
    │       └── main.yml
    ├── scvmm_core_config/
    │   ├── defaults/
    │   │   └── main.yml
    │   └── tasks/
    │       └── main.yml
    └── scvmm_livemigration/
        ├── defaults/
        │   └── main.yml
        └── tasks/
            └── main.yml
```

---

## Pré-requis

- Ansible avec collections Windows (au minimum `ansible.windows`).
- Connectivité WinRM vers les noeuds Hyper-V et le(s) serveur(s) SCVMM.
- Droits d'administration Hyper-V et droits SCVMM suffisants.
- Module PowerShell SCVMM (`VirtualMachineManager`) installé côté serveur de gestion SCVMM ciblé.

---

## Modèle d'inventaire multisite

Le fichier `inventories/multisite/group_vars/all.yml` définit:
- `live_migration`: paramètres globaux par défaut ;
- `sites`: liste des sites et clusters ;
- `scvmm`: informations de connexion au management server ;
- `scvmm_live_migration`: options de sécurité/simulation/compatibilité côté SCVMM ;
- `scvmm_core_config`: objets SCVMM hors Live Migration (host groups, bibliothèque, réseaux, clouds).

Exemple de logique:
- `live_migration` global = baseline.
- `sites.<site>.clusters[].live_migration` = surcharge locale.

Options SCVMM utiles:
- `scvmm_live_migration.manage_storage_migrations`: active la gestion du maximum de migrations de stockage quand supporté ;
- `scvmm_live_migration.manage_host_settings`: active l'application via SCVMM des options auth/perf/réseaux sur les hôtes du cluster.

---

## Exécution

### 1) Vérifier la syntaxe

```bash
ansible-playbook -i inventories/multisite/hosts.yml playbooks/configure_livemigration.yml --syntax-check
```

### 2) Simuler l'impact SCVMM sans modifier

Deux options:

```bash
ansible-playbook -i inventories/multisite/hosts.yml playbooks/configure_livemigration.yml --check
```

ou via variable:

```bash
ansible-playbook -i inventories/multisite/hosts.yml playbooks/configure_livemigration.yml -e scvmm_live_migration.check_only=true
```

### 3) Appliquer la configuration

```bash
ansible-playbook -i inventories/multisite/hosts.yml playbooks/configure_livemigration.yml
```

---

## Ce que fait le playbook

### SCVMM hors Live Migration (`scvmm_servers`)
Le rôle `scvmm_core_config` (opt-in par bloc):
- crée l'arborescence de `host_groups` ;
- crée des `library_shares` ;
- crée des `logical_networks` ;
- crée des `vm_networks` attachés à un réseau logique ;
- crée des `clouds` reliés à un ou plusieurs host groups ;
- détecte les cmdlets indisponibles et ignore proprement le bloc concerné.

### Hyper-V (`hyperv_nodes`)
Le rôle `hyperv_livemigration`:
- active/désactive la Live Migration ;
- configure le protocole d'authentification (`CredSSP` / `Kerberos`) ;
- configure l'option de performance (`TCPIP`, `Compression`, `SMB`) ;
- définit le nombre max de migrations **VM** simultanées ;
- définit le nombre max de migrations **Storage** simultanées ;
- limite les réseaux de migration si `use_any_network: false` ;
- marque `changed` uniquement en cas de drift réel.

### SCVMM (`scvmm_servers`)
Le rôle `scvmm_livemigration`:
- parcourt les clusters déclarés dans la structure multisite ;
- compare l'état courant au `MigrationMaximum` attendu ;
- peut aussi gérer `StorageMigrationMaximum` (selon support de la version SCVMM) ;
- peut propager les réglages d'authentification/performance/réseaux Live Migration vers les hôtes via SCVMM ;
- supporte un mode simulation (`--check` ou `scvmm_live_migration.check_only`) ;
- peut refuser l'application si le cluster n'est pas dans le `scvmm_host_group` attendu (`enforce_host_group: true`) ;
- détecte dynamiquement les propriétés/paramètres SCVMM disponibles pour rester compatible entre versions.

> ⚠️ Les cmdlets/paramètres SCVMM peuvent varier selon la version.
> Adaptez précisément `roles/scvmm_livemigration/tasks/main.yml` à votre version SCVMM.
